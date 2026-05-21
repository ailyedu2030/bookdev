"""
Dead Letter Queue Handler with retry logic and exponential backoff
"""

import asyncio
import logging
import os
import json
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DLQMessage:
    """Dead Letter Queue message structure"""
    original_event: Dict[str, Any]
    error: Exception
    attempts: int
    last_attempt: datetime
    handler_name: str
    traceback: str


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class DLQHandler:
    """
    Dead Letter Queue Handler

    Features:
    - Retry logic with exponential backoff
    - Error logging and alerting
    - Configurable retry behavior
    - Statistics tracking
    - Graceful failure handling (doesn't propagate exceptions)
    - Fallback logging to prevent message loss (INF-005)
    """

    # Fallback file directory when DLQ send fails
    DLQ_FALLBACK_DIR = "/var/log/bookdop/dlq_fallback"

    def __init__(
        self,
        producer,
        dlq_topic: str = "dlq",
        retry_config: Optional[RetryConfig] = None,
    ):
        self.producer = producer
        self.dlq_topic = dlq_topic
        self.retry_config = retry_config or RetryConfig()
        self._handlers: list[Callable] = []
        self._stats = {
            "total_received": 0,
            "total_retried": 0,
            "total_dlq": 0,
            "total_success": 0,
            "total_fallback_logged": 0,
        }

    def subscribe(self, handler: Callable) -> None:
        """
        Subscribe to DLQ events

        Args:
            handler: Function to call when message is sent to DLQ
        """
        self._handlers.append(handler)

    async def process_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute function with retry logic

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func

        Raises:
            Last exception if all retries exhausted
        """
        config = self.retry_config
        last_error = None

        for attempt in range(config.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Retry {attempt} succeeded")
                    self._stats["total_success"] += 1
                return result

            except Exception as e:
                last_error = e
                self._stats["total_retried"] += 1

                if attempt < config.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {config.max_retries + 1} attempts failed: {e}"
                    )

        raise last_error

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff"""
        config = self.retry_config
        delay = config.base_delay * (config.exponential_base ** attempt)
        delay = min(delay, config.max_delay)

        if config.jitter:
            import random
            delay = delay * (0.5 + random.random())

        return delay

    def _log_to_fallback_file(self, dlq_message: dict) -> str:
        """
        Log DLQ message to local fallback file.

        Args:
            dlq_message: The DLQ message to log

        Returns:
            Path to the fallback file
        """
        try:
            os.makedirs(self.DLQ_FALLBACK_DIR, exist_ok=True)

            fallback_file = os.path.join(
                self.DLQ_FALLBACK_DIR,
                f"dlq_fallback_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
            )

            with open(fallback_file, 'w') as f:
                json.dump(dlq_message, f, indent=2, default=str)

            logger.info(f"DLQ message logged to fallback file: {fallback_file}")
            return fallback_file
        except Exception as e:
            logger.error(f"Failed to write DLQ fallback log: {e}")
            # INF-005: Re-raise so caller knows fallback also failed
            raise

    async def send_to_dlq(
        self,
        event: Dict[str, Any],
        error: Exception,
        handler_name: str = "unknown",
    ) -> None:
        """
        Send failed message to Dead Letter Queue

        INF-005: Added retry mechanism for DLQ sending before fallback logging.
        Even if DLQ send fails after retries, we log to fallback file and continue
        instead of raising an exception that could crash the consumer.

        Args:
            event: The failed event
            error: The exception that caused the failure
            handler_name: Name of the handler that failed
        """
        import traceback as tb

        dlq_message = {
            "event": event,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
            "handler_name": handler_name,
            "timestamp": datetime.utcnow().isoformat(),
            "traceback": tb.format_exc(),
        }

        # INF-005: Retry DLQ sending with exponential backoff
        max_dlq_retries = 3
        base_delay = 1.0

        for attempt in range(max_dlq_retries + 1):
            try:
                await self.producer.send(self.dlq_topic, value=dlq_message)
                logger.info(f"Sent message to DLQ topic {self.dlq_topic}")
                self._stats["total_dlq"] += 1

                for handler in self._handlers:
                    try:
                        dlq_event = DLQMessage(
                            original_event=event,
                            error=error,
                            attempts=self.retry_config.max_retries + 1,
                            last_attempt=datetime.utcnow(),
                            handler_name=handler_name,
                            traceback=tb.format_exc(),
                        )
                        await handler(dlq_event)
                    except Exception as e:
                        logger.error(f"DLQ handler subscriber failed: {e}")
                return  # Success - done
            except Exception as e:
                last_error = e
                if attempt < max_dlq_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"DLQ send attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {max_dlq_retries + 1} DLQ send attempts failed: {e}"
                    )
                    # Fall through to fallback logging

        # INF-005: All retries exhausted, use fallback file logging
        try:
            fallback_path = self._log_to_fallback_file(dlq_message)
            self._stats["total_fallback_logged"] += 1
            logger.warning(
                f"DLQ send failed after {max_dlq_retries + 1} attempts, "
                f"message logged to fallback: {fallback_path}"
            )
        except Exception as fallback_error:
            # Last resort - log the raw message to application log
            logger.critical(
                f"CRITICAL: Failed to send to DLQ and fallback logging also failed. "
                f"DLQ Error: {last_error}, Fallback Error: {fallback_error}. "
                f"Event data: {json.dumps(event, default=str)[:500]}"
            )
        # Do NOT raise - continue processing to prevent consumer loop termination

    async def retry_dlq_message(
        self,
        dlq_message: Dict[str, Any],
        processor: Callable,
    ) -> Any:
        """
        Retry a message from the DLQ

        Args:
            dlq_message: Message from DLQ
            processor: Function to process the message

        Returns:
            Result of processing
        """
        event = dlq_message.get("event", {})
        error = dlq_message.get("error", {})

        logger.info(f"Retrying DLQ message: {event.get('event_type', 'unknown')}")

        return await self.process_with_retry(processor, event)

    def get_stats(self) -> Dict[str, int]:
        """Get DLQ handler statistics"""
        return self._stats.copy()

    def reset_stats(self) -> None:
        """Reset statistics"""
        self._stats = {
            "total_received": 0,
            "total_retried": 0,
            "total_dlq": 0,
            "total_success": 0,
            "total_fallback_logged": 0,
        }
