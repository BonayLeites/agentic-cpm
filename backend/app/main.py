from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import audit, config_routes, data, findings, health, summary, workflows
from app.config import settings
from app.db.session import engine, init_db
from app.middleware import DemoPinMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables. Shutdown: dispose engine."""
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(
    title="CPM Agent Accelerator",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(DemoPinMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(config_routes.router)
app.include_router(data.router)
app.include_router(workflows.router)
app.include_router(findings.router)
app.include_router(summary.router)
app.include_router(audit.router)
