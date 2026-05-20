"""
Pytest configuration and fixtures for E2E tests.
"""
import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Error as PlaywrightError
import os


@pytest.fixture(scope="session")
def browser():
    """Launch browser for the entire test session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        yield browser
        browser.close()


@pytest.fixture
def context(browser: Browser):
    """Create a new browser context for each test."""
    ctx = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN",
        extra_http_headers={
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
    )
    yield ctx
    ctx.close()


@pytest.fixture
def page(context: BrowserContext):
    """Create a new page for each test."""
    page = context.new_page()
    page.set_default_timeout(30000)
    yield page
    page.close()


@pytest.fixture
def authenticated_page(page: Page):
    """
    Login before each test and return the authenticated page.
    Uses admin credentials by default.
    """
    page.goto("http://localhost:3000/login")
    page.wait_for_load_state("networkidle")

    page.fill('input[type="email"]', "admin@example.com")
    page.fill('input[type="password"]', "password123")
    page.click('button[type="submit"]')

    page.wait_for_url("**/dashboard", timeout=10000)
    page.wait_for_load_state("networkidle")

    return page


@pytest.fixture
def screenshot_on_failure(page: Page):
    """
    Take a screenshot when a test fails.
    """
    yield
    if hasattr(pytest, "exception"):
        screenshot_dir = os.path.join(os.path.dirname(__file__), "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, f"failure_{page.url.replace('/', '_')}.png")
        try:
            page.screenshot(path=screenshot_path, full_page=True)
        except PlaywrightError:
            pass


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "auth: marks tests that require authentication")
    config.addinivalue_line("markers", "admin: marks tests that require admin role")
