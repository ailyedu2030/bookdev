"""
F19: 连贯性分析器

分析章节间的逻辑连贯性，检测逻辑缺口
"""


from f19_logic_chain.dependency_graph import DependencyGraph


class CoherenceAnalyzer:
    """连贯性分析器"""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph

    def analyze_prerequisite_chain(self, node_id: str) -> dict:
        """分析从指定节点开始的前置依赖链

        Args:
            node_id: 起始节点ID

        Returns:
            分析结果字典
        """
        if node_id not in self.graph._nodes:
            return {"complete": False, "chain": [], "missing": []}

        chain = self.graph.get_dependencies(node_id)
        complete = len(chain) > 0

        return {
            "complete": complete,
            "chain": [node_id] + chain if complete else [node_id],
            "missing": []
        }

    def detect_logical_gaps(self) -> list[dict]:
        """检测逻辑缺口

        Returns:
            缺口列表
        """
        gaps = []
        nodes = self.graph.get_all_nodes()

        for _i, node in enumerate(nodes):
            deps = self.graph.get_dependencies(node)

            if not deps:
                gaps.append({
                    "type": "orphan_node",
                    "node": node,
                    "issue": f"节点 {node} 没有前置依赖"
                })

        return gaps

    def analyze_concept_progression(self) -> dict:
        """分析概念递进的逻辑性

        Returns:
            分析结果
        """
        if self.graph.has_cycle():
            return {
                "is_logical": False,
                "reason": "检测到循环依赖"
            }

        sorted_nodes = self.graph.topological_sort()

        return {
            "is_logical": True,
            "sorted_nodes": sorted_nodes,
            "depth": len(sorted_nodes)
        }

    def find_missing_prerequisites(self, node_id: str) -> list[str]:
        """查找节点的缺失前提

        Args:
            node_id: 节点ID

        Returns:
            缺失的前提节点列表
        """
        if node_id not in self.graph._nodes:
            return []

        all_deps = set()
        to_check = [node_id]

        while to_check:
            current = to_check.pop(0)
            deps = self.graph.get_dependencies(current)

            for dep in deps:
                if dep not in all_deps:
                    all_deps.add(dep)
                    to_check.append(dep)

        all_deps.discard(node_id)
        return list(all_deps)

    def calculate_coherence_score(self) -> float:
        """计算整体连贯性评分

        Returns:
            评分 (0.0 - 1.0)
        """
        nodes = self.graph.get_all_nodes()
        if not nodes:
            return 1.0

        edges = self.graph.get_all_edges()
        if not edges:
            return 0.5

        max_edges = len(nodes) * (len(nodes) - 1) / 2
        edge_ratio = len(edges) / max_edges if max_edges > 0 else 0

        has_cycle_penalty = 0.2 if self.graph.has_cycle() else 0

        score = min(1.0, max(0.0, edge_ratio - has_cycle_penalty))
        return score

    def generate_coherence_report(self) -> dict:
        """生成连贯性报告

        Returns:
            连贯性报告
        """
        issues = self.detect_logical_gaps()

        if self.graph.has_cycle():
            issues.append({
                "type": "circular_dependency",
                "issue": "检测到循环依赖"
            })

        score = self.calculate_coherence_score()

        return {
            "overall_score": score,
            "issues": issues,
            "node_count": len(self.graph.get_all_nodes()),
            "edge_count": len(self.graph.get_all_edges()),
            "is_coherent": len(issues) == 0 and score >= 0.5,
            "sorted_order": self.graph.topological_sort() if not self.graph.has_cycle() else [],
        }

    def compare_chapters(self, chapter1: str, chapter2: str) -> dict:
        """比较两个章节的逻辑关系

        Args:
            chapter1: 章节1 ID
            chapter2: 章节2 ID

        Returns:
            比较结果
        """
        path_1_to_2 = self.graph.find_path(chapter1, chapter2)
        path_2_to_1 = self.graph.find_path(chapter2, chapter1)

        return {
            "chapter1_before_chapter2": path_1_to_2 is not None and chapter2 in path_1_to_2,
            "chapter2_before_chapter1": path_2_to_1 is not None and chapter1 in path_2_to_1,
            "direct_path_1_to_2": path_1_to_2,
            "direct_path_2_to_1": path_2_to_1,
        }
