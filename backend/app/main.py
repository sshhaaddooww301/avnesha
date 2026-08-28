"""
Main FastAPI application entry point for QDS SIEM.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import engine, Base, async_session_factory
from app.models import DetectionRule as DetectionRuleModel, SystemSetting
from app.engine.rules import RULE_REGISTRY
from app.api.settings import DEFAULT_SETTINGS
from app.websocket.manager import ws_manager

# API Routers
from app.api.dashboard import router as dashboard_router
from app.api.events import router as events_router
from app.api.threats import router as threats_router
from app.api.simulator import router as simulator_router
from app.api.ledger import router as ledger_router
from app.api.reports import router as reports_router
from app.api.pdf_report import router as pdf_report_router
from app.api.settings import router as settings_router
from app.test_lab.router import router as test_lab_router
from app.api.hardware import router as hardware_router
from app.api.defense import router as defense_router
from app.api.security import router as security_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("qds.main")


async def seed_defaults():
    """Seed detection rules and default settings if not already in DB."""
    async with async_session_factory() as session:
        # Seed rules
        for rule_id, rule_obj in RULE_REGISTRY.items():
            result = await session.execute(
                select(DetectionRuleModel).where(DetectionRuleModel.rule_id == rule_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                session.add(
                    DetectionRuleModel(
                        rule_id=rule_id,
                        name=rule_obj.name,
                        description=rule_obj.description,
                        enabled=True,
                        parameters={},
                    )
                )

        # Seed settings
        for key, val in DEFAULT_SETTINGS.items():
            result = await session.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                session.add(SystemSetting(key=key, value={"value": val}))

        await session.commit()
        logger.info("Database rules and default settings initialized.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist and seed initial defaults with retry
    logger.info("Creating database tables if not existing...")
    for attempt in range(1, 6):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await seed_defaults()
            logger.info("QDS SIEM Backend database initialized successfully.")
            break
        except Exception as e:
            logger.warning(f"Database init attempt {attempt}/5 failed: {e}. Retrying in 3s...")
            import asyncio
            await asyncio.sleep(3)
    yield
    # Shutdown
    try:
        await engine.dispose()
    except Exception:
        pass
    logger.info("Database connections closed.")


app = FastAPI(
    title="Quantum-Inspired Cyber Threat Detection (QDS) SIEM API",
    version="1.0.0",
    description="SIEM Backend for Quantum Digital Signature environments with real-time detection, statistical analysis, and tamper-evident audit ledger.",
    lifespan=lifespan,
)

# Security Middleware: IP Firewall + Rate Limiting + Security Headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.security.ip_firewall import ip_firewall
from app.security.rate_limiter import rate_limiter

class SecurityEngineMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "127.0.0.1"

        path = request.url.path

        # Whitelist health checks, openapi docs & swagger
        if path in ["/api/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"]:
            response: Response = await call_next(request)
            response.headers["X-QDS-Defense-Posture"] = "ACTIVE_HARDENED"
            return response

        # 1. IP Firewall Check for public non-private IPs
        if not ip_firewall._is_private_ip(client_ip):
            allowed, block_info = ip_firewall.check_ip(client_ip)
            if not allowed:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "IP_ACCESS_DENIED",
                        "message": "Connection terminated by QDS Security Firewall",
                        "firewall_telemetry": block_info,
                    },
                )

        # 2. Process Request
        response: Response = await call_next(request)

        # 3. Attach Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["X-QDS-Defense-Posture"] = "ACTIVE_HARDENED"
        return response

app.add_middleware(SecurityEngineMiddleware)

# CORS Configuration (Supports Localhost, Vercel & Multi-Laptop LAN Demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()},
    )

# Mount Routers
app.include_router(dashboard_router)
app.include_router(events_router)
app.include_router(threats_router)
app.include_router(simulator_router)
app.include_router(ledger_router)
app.include_router(reports_router)
app.include_router(pdf_report_router)
app.include_router(settings_router)
app.include_router(test_lab_router)
app.include_router(hardware_router)
app.include_router(defense_router)
app.include_router(security_router)


@app.get("/")
async def root():
    """Root landing endpoint with system status and quick API links."""
    return {
        "message": "Quantum Digital Signature (QDS) SIEM Backend API is Live!",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "swagger_docs": "/docs",
            "health_check": "/api/health",
            "dashboard_summary": "/api/dashboard/summary",
            "threats": "/api/threats",
            "events": "/api/events",
            "test_lab_scenarios": "/api/test-lab/scenarios",
            "defense_status": "/api/defense/status"
        }
    }


@app.get("/api/health")
async def health_check():
    """Backend health check endpoint."""
    return {
        "status": "healthy",
        "service": "QDS SIEM Detection Engine",
        "active_ws_clients": ws_manager.connection_count,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time WebSocket connection for live SOC dashboard stream with flood protection."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Enforce max payload size (16KB) to prevent buffer exhaustion attacks
            if len(data) > 16384:
                await websocket.close(code=1009, reason="Payload too large")
                break
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


@app.websocket("/ws/test-lab/{test_id}")
async def websocket_test_lab_endpoint(websocket: WebSocket, test_id: str):
    """Dedicated WebSocket stream for a specific test lab run."""
    # Sanitize test_id
    safe_test_id = test_id[:64]
    await ws_manager.connect(websocket)
    try:
        await websocket.send_text(f'{{"type":"connected","test_id":"{safe_test_id}"}}')
        while True:
            data = await websocket.receive_text()
            if len(data) > 16384:
                await websocket.close(code=1009, reason="Payload too large")
                break
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Test Lab WebSocket error for {safe_test_id}: {e}")
        ws_manager.disconnect(websocket)

