#!/usr/bin/env bash
# =============================================================================
# AI多Agent教材编写系统 - 数据库迁移脚本
# =============================================================================
set -euo pipefail

echo "==> 运行数据库迁移..."

# SQLAlchemy 迁移 (使用 Alembic 风格, 如果项目用的话)
# 当前阶段: 使用 raw SQL 确保表结构

python -c "
import os
import sys
sys.path.insert(0, '/app/src')

try:
    from sqlalchemy import create_engine, text

    db_url = (
        f\"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}\"
        f\"@{os.environ['POSTGRES_HOST']}:{os.environ.get('POSTGRES_PORT', 5432)}\"
        f\"/{os.environ.get('POSTGRES_DB', 'textbook')}\"
    )
    engine = create_engine(db_url, echo=True)

    migrations = [
        # 不可变日志表
        '''
        CREATE TABLE IF NOT EXISTS immutable_log (
            id BIGSERIAL PRIMARY KEY,
            event_type VARCHAR(128) NOT NULL,
            event_data JSONB NOT NULL DEFAULT '{}',
            event_hash VARCHAR(64) NOT NULL,
            parent_hash VARCHAR(64),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by VARCHAR(128)
        );
        CREATE INDEX IF NOT EXISTS idx_immutable_log_type ON immutable_log(event_type);
        CREATE INDEX IF NOT EXISTS idx_immutable_log_hash ON immutable_log(event_hash);
        ''',

        # 内容寻址表
        '''
        CREATE TABLE IF NOT EXISTS content_store (
            content_hash VARCHAR(64) PRIMARY KEY,
            content_type VARCHAR(64) NOT NULL,
            content_metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_content_type ON content_store(content_type);
        ''',

        # 章节表
        '''
        CREATE TABLE IF NOT EXISTS textbook_chapters (
            id VARCHAR(64) PRIMARY KEY,
            textbook_id VARCHAR(64) NOT NULL,
            chapter_index INTEGER NOT NULL,
            title VARCHAR(512) NOT NULL DEFAULT '',
            outline JSONB NOT NULL DEFAULT '{}',
            content TEXT,
            state VARCHAR(32) NOT NULL DEFAULT 'draft',
            workflow_id VARCHAR(256),
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_chapters_textbook ON textbook_chapters(textbook_id);
        CREATE INDEX IF NOT EXISTS idx_chapters_state ON textbook_chapters(state);
        ''',

        # 教材表
        '''
        CREATE TABLE IF NOT EXISTS textbooks (
            id VARCHAR(64) PRIMARY KEY,
            title VARCHAR(512) NOT NULL,
            subject VARCHAR(128) NOT NULL,
            grade_level VARCHAR(64),
            chapter_count INTEGER NOT NULL DEFAULT 0,
            status VARCHAR(32) NOT NULL DEFAULT 'draft',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_textbooks_status ON textbooks(status);
        ''',

        # 审核记录表
        '''
        CREATE TABLE IF NOT EXISTS review_records (
            id BIGSERIAL PRIMARY KEY,
            workflow_id VARCHAR(256) NOT NULL,
            chapter_id VARCHAR(64) NOT NULL,
            review_type VARCHAR(32) NOT NULL,
            approved BOOLEAN NOT NULL DEFAULT false,
            comments TEXT,
            reviewer_id VARCHAR(128) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_review_workflow ON review_records(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_review_chapter ON review_records(chapter_id);
        ''',

        # 安全扫描记录
        '''
        CREATE TABLE IF NOT EXISTS security_scans (
            id BIGSERIAL PRIMARY KEY,
            chapter_id VARCHAR(64) NOT NULL,
            scan_type VARCHAR(64) NOT NULL,
            findings JSONB NOT NULL DEFAULT '[]',
            severity VARCHAR(16) NOT NULL DEFAULT 'info',
            scan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_scans_chapter ON security_scans(chapter_id);
        ''',

        # 配置历史
        '''
        CREATE TABLE IF NOT EXISTS config_history (
            id BIGSERIAL PRIMARY KEY,
            config_key VARCHAR(256) NOT NULL,
            config_value TEXT NOT NULL,
            changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            changed_by VARCHAR(128)
        );
        CREATE INDEX IF NOT EXISTS idx_config_key ON config_history(config_key);
        ''',

        # 血缘追踪
        '''
        CREATE TABLE IF NOT EXISTS lineage_records (
            id BIGSERIAL PRIMARY KEY,
            source_id VARCHAR(64) NOT NULL,
            target_id VARCHAR(64) NOT NULL,
            relation_type VARCHAR(64) NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_lineage_source ON lineage_records(source_id);
        CREATE INDEX IF NOT EXISTS idx_lineage_target ON lineage_records(target_id);
        '''
    ]

    with engine.connect() as conn:
        for sql in migrations:
            conn.execute(text(sql))
            conn.commit()

    print('✅ 所有数据库迁移完成')
except Exception as e:
    print(f'❌ 迁移失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
