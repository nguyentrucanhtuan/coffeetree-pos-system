"""CoffeeTree API — main application entry point.

- Lifespan: auto-seed superuser from .env
- JWTMiddleware: inject request.state auth info
- Routers: auth + system (CMS Core)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from .config import settings
from .database import AsyncSessionLocal, engine, Base
from auth.middleware import JWTMiddleware
from auth.models import User
from auth.utils import hash_password
from system.models import SystemSetting  # noqa: F401 — ensures table is created

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    # Startup: create tables + seed superuser
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Auto-seed superuser if users table is empty
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        if not result.scalar_one_or_none():
            superuser = User(
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                full_name="Admin",
                is_active=True,
                is_superuser=True,
                email_verified=True,
            )
            db.add(superuser)
            await db.commit()
            logger.info("✅ Superuser seeded: %s", settings.ADMIN_EMAIL)
        else:
            logger.info("ℹ️  Users table not empty, skipping superuser seed")

    # Auto-seed module settings from _settings class attribute
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select as sa_select

        # REGISTERED_MODULES is defined at module level below — safe to reference
        for module_cls in REGISTERED_MODULES:
            if not module_cls._settings:
                continue
            for s in module_cls._settings:
                existing = await db.execute(
                    sa_select(SystemSetting).where(
                        SystemSetting.module_name == module_cls._module_name,
                        SystemSetting.key == s["key"],
                    )
                )
                if not existing.scalar_one_or_none():
                    db.add(SystemSetting(
                        module_name=module_cls._module_name,
                        key=s["key"],
                        label=s.get("label", s["key"]),
                        value=str(s.get("default", "")),
                        value_type=s.get("type", "string"),
                    ))
        await db.commit()

    yield

    # Shutdown
    await engine.dispose()



app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

# OpenAPI security scheme — shows Authorize 🔓 button in Swagger UI
from fastapi.openapi.utils import get_openapi


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    # Apply globally to all endpoints
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi

# Middleware — order matters: CORS must be outermost
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(JWTMiddleware)

# Routers — explicit registration (constitution: Principle VIII)
from auth.router import router as auth_router
from system.router import router as system_router

app.include_router(auth_router)
app.include_router(system_router)

# TRCFBaseModule business modules — explicit registration
from modules.products import Product, Category, Unit
from modules.employees import Employee, Department

# HR
from modules.employees import Employee
# from modules.attendance import Attendance

# CRM
from modules.customers import Customer

# Warehouse
from modules.warehouse import Warehouse, StockMovement
from modules.bom import BoM, BoMLine

# POS
from modules.pos import SalesPoint, Order, OrderItem
from modules.payment_methods import PaymentMethod
from modules.area import Zone, DiningTable
from modules.invoices import Tax

app.include_router(Product.router())
app.include_router(Category.router())
app.include_router(Unit.router())
app.include_router(Tax.router())
app.include_router(Employee.router())
app.include_router(Department.router())
# app.include_router(Attendance.router())
app.include_router(Customer.router())
app.include_router(Warehouse.router())
app.include_router(StockMovement.router())
app.include_router(BoM.router())
app.include_router(BoMLine.router())
app.include_router(SalesPoint.router())
app.include_router(Order.router())
app.include_router(OrderItem.router())
app.include_router(PaymentMethod.router())
app.include_router(Zone.router())
app.include_router(DiningTable.router())
app.include_router(Tax.router())

# Module registry for /modules/menu endpoint
REGISTERED_MODULES: list[type] = [
    Unit, Category, Product,
    Employee, Department,
    Customer,
    Warehouse, StockMovement, BoM, BoMLine,
    SalesPoint, Order, OrderItem, PaymentMethod, Zone, DiningTable,
    Tax,
]

# Static files — serve uploads
from fastapi.staticfiles import StaticFiles

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/")
async def root() -> dict:
    return {
        "success": True,
        "data": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
        },
        "message": None,
    }
