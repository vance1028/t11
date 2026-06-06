from fastapi import APIRouter

from app.api import hospitals, inventory, requests, dispatches, dashboard, compatibility

api_router = APIRouter()

api_router.include_router(hospitals.router, prefix="/hospitals", tags=["医院管理"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["库存管理"])
api_router.include_router(requests.router, prefix="/requests", tags=["用血申请"])
api_router.include_router(dispatches.router, prefix="/dispatches", tags=["调拨管理"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["看板统计"])
api_router.include_router(compatibility.router, prefix="/compatibility", tags=["相容矩阵"])
