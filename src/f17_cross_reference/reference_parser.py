"""
F17: 引用解析器

解析文本中的交叉引用标记:
- [@def:target_id] - 定义引用
- [@app:target_id] - 应用引用
- [@cmp:target_id] - 对比引用
- [@cite:doi] - 文献引用
"""

import re
from typing import NamedTuple


class ReferencePattern:
    """引用模式类型"""
    DEFINITION_REF = "definition_ref"
    APPLICATION_REF = "application_ref"
    COMPARISON_REF = "comparison_ref"
    CITATION_REF = "citation_ref"


class ParsedReference(NamedTuple):
    """解析后的引用"""
    ref_type: str
    target_id: str
    source_location: tuple[int, int]  # (line, column)
    context: str


class ReferenceParser:
    """引用解析器"""

    PATTERNS = {
        ReferencePattern.DEFINITION_REF: r'\[@def:([^\]]+)\]',
        ReferencePattern.APPLICATION_REF: r'\[@app:([^\]]+)\]',
        ReferencePattern.COMPARISON_REF: r'\[@cmp:([^\]]+)\]',
        ReferencePattern.CITATION_REF: r'\[@cite:([^\]]+)\]',
    }

    def __init__(self):
        self._compiled_patterns = {
            ref_type: re.compile(pattern)
            for ref_type, pattern in self.PATTERNS.items()
        }

    def parse_references(self, content: str) -> list[ParsedReference]:
        """解析文本中的所有引用"""
        references = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, start=1):
            for ref_type, pattern in self._compiled_patterns.items():
                for match in pattern.finditer(line):
                    target_id = match.group(1)
                    col = match.start()

                    context = self._extract_context(line, match.start(), match.end())

                    references.append(ParsedReference(
                        ref_type=ref_type,
                        target_id=target_id,
                        source_location=(line_num, col),
                        context=context
                    ))

        return references

    def _extract_context(self, line: str, match_start: int, match_end: int) -> str:
        """提取引用周围的上下文"""
        context_chars = 20
        start = max(0, match_start - context_chars)
        end = min(len(line), match_end + context_chars)
        return line[start:end].strip()

    def detect_circular_reference(self, references: list[tuple[str, str]]) -> bool:
        """检测循环引用

        Args:
            references: [(source_id, target_id), ...] 引用对列表

        Returns:
            True if circular reference exists
        """
        graph = {}
        for source, target in references:
            if source not in graph:
                graph[source] = []
            graph[source].append(target)

        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True

        return False
