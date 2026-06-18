"""Main application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from src.config import get_settings
from src.database import init_database
from src.scheduler import init_scheduler
from src.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()

    # Initialize database
    logger.info("Initializing database...")
    init_database()

    # Initialize and start scheduler
    logger.info("Starting scheduler...")
    scheduler = init_scheduler()
    scheduler.start()

    logger.info(f"Application started on http://localhost:{settings.port}")
    logger.info("Dashboard available at http://localhost:8000/")

    yield

    # Shutdown
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()


# Create FastAPI app
app = FastAPI(
    title="Application Status Dashboard",
    description="Real-time monitoring dashboard for external service status pages",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API routes
app.include_router(router)

# Serve static files
try:
    app.mount("/static", StaticFiles(directory="src/static"), name="static")
except RuntimeError:
    logger.warning("Static files directory not found, skipping static mount")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the dashboard HTML."""
    try:
        with open("src/static/dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <html>
                <head><title>Status Dashboard</title></head>
                <body>
                    <h1>Application Status Dashboard</h1>
                    <p>Dashboard is starting up...</p>
                    <p>API available at <a href="/api/status">/api/status</a></p>
                </body>
            </html>
            """,
            status_code=200,
        )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower(),
    )
