from fastapi import APIRouter
from .v1.endpoints.generate import router as generate_router


router = APIRouter()
router.include_router(generate_router, prefix="/v1")
