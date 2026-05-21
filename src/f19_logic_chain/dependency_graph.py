"""
F19: 依赖图

提供图数据结构，支持节点和边的操作
"""



class DependencyGraph:
    """依赖图"""

    def __init__(self):
        self._nodes: set[str] = set()
        self._edges: list[tuple[str, str]] = []
        self._adjacency: dict[str, list[str]] = {}
        self._reverse_adjacency: dict[str, list[str]] = {}

    def add_node(self, node_id: str) -> None:
        """添加节点"""
        self._nodes.add(node_id)
        if node_id not in self._adjacency:
            self._adjacency[node_id] = []
        if node_id not in self._reverse_adjacency:
            self._reverse_adjacency[node_id] = []

    def add_edge(self, source: str, target: str) -> None:
        """添加边"""
        self.add_node(source)
        self.add_node(target)

        if target not in self._adjacency[source]:
            self._adjacency[source].append(target)

        if source not in self._reverse_adjacency[target]:
            self._reverse_adjacency[target].append(source)

        self._edges.append((source, target))

    def has_node(self, node_id: str) -> bool:
        """检查节点是否存在"""
        return node_id in self._nodes

    def has_edge(self, source: str, target: str) -> bool:
        """检查边是否存在"""
        return (source, target) in self._edges

    def get_dependencies(self, node_id: str) -> list[str]:
        """获取节点的所有依赖 (该节点指向的节点)"""
        return self._adjacency.get(node_id, [])

    def get_dependents(self, node_id: str) -> list[str]:
        """获取依赖该节点的所有节点 (指向该节点的节点)"""
        return self._reverse_adjacency.get(node_id, [])

    def get_independent_nodes(self) -> list[str]:
        """获取独立节点 (没有依赖也没有被依赖)"""
        independent = []
        for node in self._nodes:
            if not self._adjacency.get(node) and not self._reverse_adjacency.get(node):
                independent.append(node)
        return independent

    def find_path(self, start: str, end: str) -> list[str] | None:
        """查找从start到end的路径"""
        if start not in self._nodes or end not in self._nodes:
            return None

        if start == end:
            return [start]

        visited = {start}
        queue = [(start, [start])]

        while queue:
            current, path = queue.pop(0)

            for neighbor in self._adjacency.get(current, []):
                if neighbor == end:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def get_all_paths(self, start: str, end: str) -> list[list[str]]:
        """查找从start到end的所有路径"""
        if start not in self._nodes or end not in self._nodes:
            return []

        paths = []

        def dfs(current: str, path: list[str]):
            if current == end:
                paths.append(path[:])
                return

            for neighbor in self._adjacency.get(current, []):
                if neighbor not in path:
                    path.append(neighbor)
                    dfs(neighbor, path)
                    path.pop()

        dfs(start, [start])
        return paths

    def get_all_nodes(self) -> list[str]:
        """获取所有节点"""
        return list(self._nodes)

    def get_all_edges(self) -> list[tuple[str, str]]:
        """获取所有边"""
        return self._edges.copy()

    def topological_sort(self) -> list[str]:
        """拓扑排序"""
        in_degree = {node: 0 for node in self._nodes}
        for _source, targets in self._adjacency.items():
            for target in targets:
                in_degree[target] += 1

        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in self._adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result

    def has_cycle(self) -> bool:
        """检测是否有环"""
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self._adjacency.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in self._nodes:
            if node not in visited:
                if dfs(node):
                    return True

        return False
