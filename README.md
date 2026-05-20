# AI多Agent教材编写系统

基于MiniMax-M2.7的AI多智能体协同教材编写系统，支持20万汉字（约100万Tokens）教材生成。

## 技术栈

- **后端**: Python 3.11+ / FastAPI / SQLAlchemy 2.0
- **工作流**: Temporal + Redis Streams
- **数据库**: PostgreSQL 15 + Qdrant向量检索
- **前端**: React 18 + TypeScript + Ant Design 5
- **监控**: Prometheus + Grafana

## 功能模块 (F00-F32)

| 模块 | 名称 | 状态 |
|------|------|------|
| F00 | Kafka事件总线 | ✅ |
| F01 | 不可变日志 | ✅ |
| F02 | 上下文预算管理 | ✅ |
| F03 | 内容寻址 | ✅ |
| F04 | Temporal工作流 | ✅ |
| F05 | 知识图谱(内存) | ✅ |
| ... | ... | ... |
| F31 | MiniMax客户端 | ✅ |
| F32 | PG知识图谱 | ✅ |

## 快速开始

```bash
# 安装依赖
pip install -e .

# 运行测试
pytest src/ --cov=src

# 启动开发服务器
docker-compose -f docker-compose.dev.yml up
```

## 测试覆盖

```
2064 tests passed
96.67% coverage (要求 60%)
```

## 项目结构

```
src/
├── api/           # FastAPI路由
├── db/            # SQLAlchemy模型和仓库
├── pipeline/      # 教材生成流水线
└── f00-f32/       # 32个功能模块

tests/             # 测试套件
frontend/          # React前端
config/            # 配置文件
```

## License

Proprietary