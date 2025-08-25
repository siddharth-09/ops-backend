"""
API v1 routes for OpsFlow Guardian 2.0
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    agents,
    workflows,
    approvals,
    audit,
    analytics,
    email_config,
    company
)
from app.api.v1.auth import router as google_auth_router

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    google_auth_router,
    tags=["Google Authentication"]
)

api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["Agents"]
)

api_router.include_router(
    workflows.router,
    prefix="/workflows",
    tags=["Workflows"]
)

api_router.include_router(
    approvals.router,
    prefix="/approvals",
    tags=["Approvals"]
)

api_router.include_router(
    audit.router,
    prefix="/audit",
    tags=["Audit"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"]
)

api_router.include_router(
    email_config.router,
    tags=["Email Configuration"]
)

api_router.include_router(
    company.router,
    tags=["Company Profile"]
)
