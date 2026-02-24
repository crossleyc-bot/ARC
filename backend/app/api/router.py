from fastapi import APIRouter

from app.api import analysis, canonical, connections, exports, inventory, projects

api_router = APIRouter(prefix="/api")

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(connections.router, tags=["connections"])
api_router.include_router(inventory.router, tags=["inventory"])
api_router.include_router(analysis.router, tags=["analysis"])
api_router.include_router(canonical.router, tags=["canonical"])
api_router.include_router(exports.router, tags=["exports"])
