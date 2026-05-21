"""
F17: 引用解析器

将引用解析为实际的图谱节点，验证引用有效性
"""

from typing import Any

from f05_knowledge_graph.knowledge_graph import KnowledgeGraph


class ReferenceResolver:
    """引用解析器"""

    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph

    def resolve(self, target_id: str, ref_type: str) -> Any | None:
        """解析引用到目标节点

        Args:
            target_id: 目标节点ID
            ref_type: 引用类型

        Returns:
            目标节点，如果不存在返回None
        """
        return self.kg.get_node(target_id)

    def validate_reference_chain(
        self,
        source_id: str,
        referenced_target: str | None = None
    ) -> bool:
        """验证引用链完整性

        Args:
            source_id: 源节点ID
            referenced_target: 指定的目标节点ID (可选)

        Returns:
            True if chain is valid
        """
        edges = self.kg.get_edges(node_id=source_id, edge_type="REFERENCES")

        if not edges:
            return referenced_target is None

        if referenced_target is None:
            return len(edges) > 0

        for edge in edges:
            if edge.target == referenced_target:
                return True

        return False

    def get_all_references_from_section(self, section_id: str) -> list:
        """获取章节的所有引用

        Args:
            section_id: 章节ID

        Returns:
            引用列表
        """
        edges = self.kg.get_edges(node_id=section_id)
        references = []
        for edge in edges:
            if edge.edge_type in ("REFERENCES", "DEFINES", "USES", "FOLLOWS"):
                target = self.kg.get_node(edge.target)
                if target:
                    references.append({
                        "source": section_id,
                        "target": edge.target,
                        "target_title": target.title,
                        "reference_type": edge.properties.get("reference_type"),
                        "context": edge.properties.get("context"),
                        "edge_type": edge.edge_type,
                    })
        return references

    def get_all_references_to_section(self, section_id: str) -> list:
        """获取引用到章节的所有来源

        Args:
            section_id: 目标章节ID

        Returns:
            引用列表
        """
        edges = self.kg.get_edges(node_id=section_id)
        references = []

        for edge in edges:
            if edge.edge_type in ("REFERENCES", "DEFINES", "USES"):
                if edge.target == section_id:
                    source = self.kg.get_node(edge.source)
                    if source:
                        references.append({
                            "source": edge.source,
                            "source_title": source.title,
                            "target": section_id,
                            "reference_type": edge.properties.get("reference_type"),
                            "context": edge.properties.get("context"),
                        })

        return references

    def check_reference_consistency(self, section_ids: list[str]) -> dict:
        """检查章节引用一致性

        Args:
            section_ids: 章节ID列表

        Returns:
            一致性检查结果
        """
        issues = []
        all_references = set()

        for section_id in section_ids:
            refs = self.get_all_references_from_section(section_id)
            for ref in refs:
                if ref["target"] not in section_ids:
                    issues.append({
                        "type": "external_reference",
                        "source": section_id,
                        "target": ref["target"],
                    })
                ref_key = (section_id, ref["target"])
                if ref_key in all_references:
                    issues.append({
                        "type": "duplicate_reference",
                        "source": section_id,
                        "target": ref["target"],
                    })
                all_references.add(ref_key)

        return {
            "is_consistent": len(issues) == 0,
            "issues": issues,
            "total_references": len(all_references),
        }

    def generate_reference_report(self) -> dict:
        """生成引用报告

        Returns:
            引用统计报告
        """
        edges = self.kg.get_edges()
        references = [e for e in edges if e.edge_type == "REFERENCES"]

        by_type = {}
        for edge in references:
            ref_type = edge.properties.get("reference_type", "unknown")
            by_type[ref_type] = by_type.get(ref_type, 0) + 1

        return {
            "total_references": len(references),
            "by_type": by_type,
            "unique_sources": len({e.source for e in references}),
            "unique_targets": len({e.target for e in references}),
        }
