from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.utils.redis import init_redis, close_redis
from app.interfaces.user_repository import IUserRepository
from app.crud.user import UserRepository
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

openapi_url = f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=openapi_url
)

# Set all CORS enabled origins only if not handled by Gateway/Proxy
if settings.BACKEND_CORS_ORIGINS_LIST and settings.ENVIRONMENT != "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS_LIST,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

# Dependency Injection Overrides
async def get_user_crud(db: AsyncSession = Depends(get_db)) -> IUserRepository:
    return UserRepository(session=db)

from prometheus_fastapi_instrumentator import Instrumentator

app.dependency_overrides[IUserRepository] = get_user_crud

# LỖ HỔNG ĐƯỢC VÁ: Nhóm các endpoint có chứa ID lại thành một template duy nhất (Chống Tràn RAM)
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_group_untemplated=False,
    inprogress_name="inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app).expose(app, include_in_schema=False)
@app.on_event("startup")
async def startup_event():
    await init_redis()


@app.on_event("shutdown")
async def shutdown_event():
    await close_redis()


@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

@app.get("/health/liveness", tags=["health"])
async def liveness_probe():
    """Shallow check for K8s Liveness Probe. Indicates if Uvicorn is responsive."""
    return {"status": "alive"}

@app.get("/health/readiness", tags=["health"])
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """Deep check for K8s Readiness Probe. Validates DB and Redis connections."""
    from app.utils.redis import redis_client
    from sqlalchemy import text
    try:
        # DB Check
        await db.execute(text("SELECT 1"))
        # Redis Check
        if not redis_client:
            raise Exception("Redis client not initialized")
        await redis_client.ping()
        return {"status": "ready"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Service Unavailable")