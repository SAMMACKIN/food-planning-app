from fastapi import APIRouter
from app.api.endpoints import auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])


@api_router.get("/")
async def api_root():
    return {"message": "Food Planning App API v1"}