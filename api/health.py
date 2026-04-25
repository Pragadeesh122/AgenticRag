"""Health check endpoints for Kubernetes probes."""

import asyncio
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

TIMEOUT = 3  # seconds per dependency check


@router.get("/health")
async def liveness():
    """Liveness probe. Returns 200 if the process is alive."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness():
    """Readiness probe. Checks PostgreSQL, Redis, and MinIO connectivity."""
    checks = {}

    # PostgreSQL
    try:
        from database.core import async_session_maker

        async with async_session_maker() as session:
            await asyncio.wait_for(
                session.execute(text("SELECT 1")), timeout=TIMEOUT
            )
        checks["postgres"] = "ok"
    except Exception as e:
        logger.warning(f"readiness: postgres check failed: {e}")
        checks["postgres"] = "fail"

    # Redis
    try:
        from memory.redis_client import redis_client

        await asyncio.wait_for(
            asyncio.to_thread(redis_client.ping), timeout=TIMEOUT
        )
        checks["redis"] = "ok"
    except Exception as e:
        logger.warning(f"readiness: redis check failed: {e}")
        checks["redis"] = "fail"

    # MinIO — verify connectivity only, not bucket existence.
    # The bucket is created by a post-install hook; checking it here would
    # deadlock helm install --wait (readiness blocks until hook runs, hook
    # blocks until readiness passes).
    try:
        from clients import minio_client

        await asyncio.wait_for(
            asyncio.to_thread(minio_client.list_buckets),
            timeout=TIMEOUT,
        )
        checks["minio"] = "ok"
    except Exception as e:
        logger.warning(f"readiness: minio check failed: {e}")
        checks["minio"] = "fail"

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503
    return JSONResponse(
        content={"status": "ok" if all_ok else "degraded", "checks": checks},
        status_code=status_code,
    )
