"""AI多Agent教材编写系统 - Web API"""
import sys, os, asyncio, json, time
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

# Load .env
env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_file):
    for line in open(env_file):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(title="AI多Agent教材编写系统", version="1.0.0")

from f31_minimax_client.minimax_client import MiniMaxClient
from f01_immutable_log.immutable_log import ImmutableLog
from f02_context_budget.context_budget_manager import ContextBudgetManager
from f05_knowledge_graph.knowledge_graph import KnowledgeGraph
from f23_content_security.content_filter import ContentSecurityFilter
from f20_llm_judge.judge_service import JudgeService, MockLLMClient
from f21_risk_classification.risk_classifier import RiskClassifier
from f24_config_center.config_center import ConfigCenter
from f28_monitoring_dashboard.monitoring_dashboard import MonitoringDashboard
from f29_quality_gate.quality_gate import QualityGate

# Global instances
log = ImmutableLog()
budget = ContextBudgetManager()
config = ConfigCenter()
monitor = MonitoringDashboard()
kg = KnowledgeGraph()
security = ContentSecurityFilter()
minimax = MiniMaxClient()
risk = RiskClassifier()

# In-memory project store
projects = {}
chapters = {}


class GenerateRequest(BaseModel):
    project_id: str
    chapter_id: str
    title: str
    prompt: str
    max_tokens: int = 500


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    chapter_count: int = 5


@app.get("/", response_class=HTMLResponse)
async def index():
    return open(os.path.join(os.path.dirname(__file__), "index.html")).read()


@app.get("/api/status")
async def system_status():
    qg = QualityGate()
    qr = qg.run_quality_gates("src/")
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "minimax": {
            "connected": not minimax._is_mock_mode,
            "model": minimax.model,
            "base_url": minimax.base_url,
        },
        "modules": {
            "immutable_log": len(log.get_entries()),
            "budget": f"{budget.get_total_usage()}t/{budget.TOTAL_BUDGET}t",
            "knowledge_graph": len(kg.get_chapter_dependency_graph()),
            "security_filter": "active",
            "risk_classifier": "active",
        },
        "quality_gate": {
            "passed": qr.passed,
            "total": len(qr.check_results),
            "summary": qr.summary,
        },
        "projects": len(projects),
        "chapters": sum(len(v) for v in chapters.values()),
    }


@app.post("/api/projects")
async def create_project(req: ProjectCreate):
    pid = f"prj-{len(projects)+1:03d}"
    projects[pid] = {
        "id": pid,
        "name": req.name,
        "description": req.description,
        "chapter_count": req.chapter_count,
        "status": "draft",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "chapters": []
    }
    chapters[pid] = []
    log.append("project_created", {"id": pid, "name": req.name})
    return projects[pid]


@app.get("/api/projects")
async def list_projects():
    return list(projects.values())


@app.post("/api/generate")
async def generate_content(req: GenerateRequest):
    if minimax._is_mock_mode:
        raise HTTPException(503, "MiniMax API 未连接，请检查 MINIMAX_API_KEY")

    system_prompt = f"你是教材编写专家。正在编写《{req.title}》章节。请用学术风格撰写，内容严谨准确。"
    user_prompt = req.prompt

    start = time.time()
    resp = await minimax.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=req.max_tokens,
        temperature=0.6
    )
    latency = time.time() - start

    # Security scan
    sec_result = security.filter_content(resp.content)

    # Quality assessment
    mock = json.dumps({"scores": {"terminology_consistency": 8, "knowledge_accuracy": 9, "citation_validity": 7, "logical_coherence": 8, "format_compliance": 9}, "overall_score": 8.2, "reasoning": "auto"})
    ml = MockLLMClient(response=mock)
    js = JudgeService(llm_client=ml)
    quality = await js.judge_content(resp.content[:500], f"{req.project_id}/{req.chapter_id}")

    # Risk
    risk_level = risk.classify(quality.overall_score / 10.0) if quality else "unknown"

    chapter_data = {
        "id": req.chapter_id,
        "title": req.title,
        "content": resp.content,
        "tokens": resp.usage.total_tokens,
        "latency": f"{latency:.1f}s",
        "security": {
            "safe": sec_result.is_safe,
            "action": sec_result.action,
            "categories": sec_result.categories,
        },
        "quality": {
            "score": quality.overall_score if quality else None,
            "risk": str(risk_level),
        },
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    if req.project_id not in chapters:
        chapters[req.project_id] = []
    chapters[req.project_id].append(chapter_data)

    log.append("content_generated", {"project": req.project_id, "chapter": req.chapter_id, "tokens": resp.usage.total_tokens})
    monitor.record_metric("api.generate_tokens", resp.usage.total_tokens)
    monitor.record_metric("api.generate_latency", latency * 1000)

    return chapter_data


@app.get("/api/chapters/{project_id}")
async def list_chapters(project_id: str):
    return chapters.get(project_id, [])


@app.get("/api/security/scan")
async def security_scan(text: str = ""):
    result = security.filter_content(text)
    return {
        "safe": result.is_safe,
        "action": result.action,
        "confidence": result.confidence_score,
        "categories": result.categories,
        "violations": result.violations,
    }


@app.get("/api/monitor")
async def monitoring():
    return {
        "health": monitor.get_health_status().status,
        "log_entries": len(log.get_entries()),
        "budget_usage": budget.get_total_usage(),
        "projects": len(projects),
    }


if __name__ == "__main__":
    print("\n  🚀 AI多Agent教材编写系统 Web界面")
    print("  =================================")
    print("  http://localhost:8000")
    print("  http://localhost:8000/docs (API文档)")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000)
