from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes import router
from app.db import get_session

app = FastAPI(title="SentinelOps", version="0.1.0")
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)):
    await session.execute(text("SELECT 1"))
    return {"status": "ready"}

