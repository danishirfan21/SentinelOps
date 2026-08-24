from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes import router
from app.db import get_session
from app.config import get_settings

app = FastAPI(title="SentinelOps", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().allowed_origins(), allow_credentials=False, allow_methods=["GET", "POST", "PATCH"], allow_headers=["Content-Type"])
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)):
    await session.execute(text("SELECT 1"))
    return {"status": "ready"}

