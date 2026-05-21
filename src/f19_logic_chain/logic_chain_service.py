"""
F19: 逻辑链服务

维护章节间的逻辑依赖关系，提供依赖分析、拓扑排序功能
"""

from dataclasses import dataclass
from enum import Enum


class DependencyType(Enum):
    PREREQUISITE = "prerequisite"
    SEQUENTIAL = "sequential"
    OPTIONAL = "optional"


@dataclass
class Dependency:
    """依赖关系"""

    source: str
    target: str
    dependency_type: DependencyType = DependencyType.SEQUENTIAL


@dataclass
class Issue:
    """问题"""

    type: str
    description: str
    source: str | None = None
    target: str | None = None


@dataclass
class AddDependencyResult:
    """添加依赖结果"""

    success: bool
    dependency: Dependency | None = None
    error: str | None = None


class LogicChainService:
    """逻辑链服务"""

    def __init__(self):
        self._dependencies: list[Dependency] = []
        self._adjacency: dict[str, list[str]] = {}
        self._reverse_adjacency: dict[str, list[str]] = {}

    def add_dependency(
        self, source: str, target: str, dependency_type: DependencyType = DependencyType.SEQUENTIAL
    ) -> AddDependencyResult:
        """添加依赖关系"""
        dependency = Dependency(source=source, target=target, dependency_type=dependency_type)

        self._dependencies.append(dependency)

        if source not in self._adjacency:
            self._adjacency[source] = []
        self._adjacency[source].append(target)

        if target not in self._reverse_adjacency:
            self._reverse_adjacency[target] = []
        self._reverse_adjacency[target].append(source)

        return AddDependencyResult(success=True, dependency=dependency)

    def get_dependencies(self, node_id: str) -> list[Dependency]:
        """获取节点的所有依赖"""
        return [d for d in self._dependencies if d.source == node_id]

    def get_dependents(self, node_id: str) -> list[Dependency]:
        """获取依赖该节点的所有节点"""
        return [d for d in self._dependencies if d.target == node_id]

    def get_dependency_chain(self, node_id: str) -> list[str]:
        """获取依赖链"""
        visited = set()
        chain = []

        def dfs(current: str):
            if current in visited:
                return
            visited.add(current)
            chain.append(current)
            for neighbor in self._adjacency.get(current, []):
                dfs(neighbor)

        dfs(node_id)
        return chain

    def get_topological_order(self) -> list[str]:
        """获取拓扑排序后的节点顺序"""
        in_degree = {}
        for node_id in self._adjacency:
            if node_id not in in_degree:
                in_degree[node_id] = 0
            for neighbor in self._adjacency[node_id]:
                if neighbor not in in_degree:
                    in_degree[neighbor] = 0
                in_degree[neighbor] += 1

        queue = [n for n in in_degree if in_degree[n] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in self._adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result

    def validate_dependency_graph(self) -> bool:
        """验证依赖图是否有环"""
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self._adjacency.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in self._adjacency:
            if node not in visited:
                if has_cycle(node):
                    return False

        return True

    def detect_issues(self) -> list[Issue]:
        """检测依赖图中的问题"""
        issues = []

        if not self.validate_dependency_graph():
            issues.append(Issue(type="circular_dependency", description="检测到循环依赖"))

        for source, targets in self._adjacency.items():
            for target in targets:
                if source == target:
                    issues.append(
                        Issue(
                            type="self_reference", description=f"节点 {source} 引用自身", source=source, target=target
                        )
                    )

        return issues

    def export(self) -> dict:
        """导出逻辑链"""
        return {
            "dependencies": [
                {
                    "source": d.source,
                    "target": d.target,
                    "dependency_type": d.dependency_type.value,
                }
                for d in self._dependencies
            ]
        }

    def import_(self, data: dict) -> None:
        """导入逻辑链"""
        self._dependencies.clear()
        self._adjacency.clear()
        self._reverse_adjacency.clear()

        for dep_data in data.get("dependencies", []):
            dep_type = DependencyType(dep_data.get("dependency_type", "sequential"))
            self.add_dependency(dep_data["source"], dep_data["target"], dep_type)

    def generate_logic_chain_document(self) -> str:
        """生成逻辑链文档"""
        ordered = self.get_topological_order()
        lines = ["# 逻辑链文档\n"]

        for _i, node in enumerate(ordered):
            deps = self.get_dependencies(node)
            if deps:
                dep_ids = [d.target for d in deps]
                lines.append(f"## {node}")
                lines.append(f"依赖: {', '.join(dep_ids)}\n")
            else:
                lines.append(f"## {node} (起点)")
                lines.append("无前置依赖\n")

        return "\n".join(lines)
