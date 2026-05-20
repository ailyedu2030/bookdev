-- F32: PostgreSQL 知识图谱数据库 Schema
-- 支持 JSONB 动态属性存储和图遍历操作

-- 节点表
CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 边表
CREATE TABLE IF NOT EXISTS graph_edges (
    id SERIAL PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_edges_source FOREIGN KEY (source_id)
        REFERENCES graph_nodes(id) ON DELETE CASCADE,
    CONSTRAINT fk_edges_target FOREIGN KEY (target_id)
        REFERENCES graph_nodes(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_nodes_type ON graph_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_type ON graph_edges(edge_type);
CREATE INDEX IF NOT EXISTS idx_edges_source_target ON graph_edges(source_id, target_id);
CREATE INDEX IF NOT EXISTS idx_nodes_properties ON graph_nodes USING GIN (properties);
CREATE INDEX IF NOT EXISTS idx_edges_properties ON graph_edges USING GIN (properties);

-- 更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 节点表更新触发器
DROP TRIGGER IF EXISTS trigger_nodes_updated_at ON graph_nodes;
CREATE TRIGGER trigger_nodes_updated_at
    BEFORE UPDATE ON graph_nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 图遍历辅助函数：获取邻居节点
CREATE OR REPLACE FUNCTION get_neighbors(node_id TEXT, max_depth INT DEFAULT 1)
RETURNS TABLE (
    source_id TEXT,
    target_id TEXT,
    edge_type TEXT,
    depth INT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE neighbors AS (
        SELECT
            e.source_id,
            e.target_id,
            e.edge_type,
            1 AS depth
        FROM graph_edges e
        WHERE e.source_id = node_id OR e.target_id = node_id

        UNION ALL

        SELECT
            e.source_id,
            e.target_id,
            e.edge_type,
            n.depth + 1
        FROM graph_edges e
        INNER JOIN neighbors n ON (
            e.source_id = n.target_id
            OR e.target_id = n.source_id
            OR e.source_id = n.source_id
            OR e.target_id = n.target_id
        )
        WHERE n.depth < max_depth
    )
    SELECT DISTINCT n.source_id, n.target_id, n.edge_type, n.depth
    FROM neighbors n;
END;
$$ LANGUAGE plpgsql;
