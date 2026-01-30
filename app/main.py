from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html

from app.db import Base, engine
from app.routes_auth import router as auth_router
from app.routes_bank import router as bank_router

# Create tables (MVP approach). Later you can replace this with migrations (Alembic).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Northbridge Secure Banking MVP",
    version="0.1.0",
    description="""
### Northbridge Digital Bank — Enterprise Technology Risk Assessment MVP

This API demonstrates security controls aligned with an enterprise risk assessment:
- JWT Authentication (OAuth2 password flow)
- Role-Based Access Control (RBAC: user/admin)
- Audit Logging for key events (register/login/transfer/etc.)
- Transaction tracking (deposits/transfers)

**Quick Start**
1. Register a user: `POST /auth/register`
2. Login: `POST /auth/login` (Swagger uses **username** field as your email)
3. Copy `access_token`
4. In Swagger, click **Authorize** → paste token (no quotes)
5. Call protected endpoints like `GET /bank/me`
""",
)

# Routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(bank_router, prefix="/bank", tags=["bank"])

# Pretty docs homepage (ReDoc)
@app.get("/", include_in_schema=False)
def docs_home():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Northbridge API Documentation",
    )

@app.get("/health", tags=["default"])
def health():
    return {"status": "ok"}
