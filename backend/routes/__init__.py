from .auth import router as auth_router
from .customers import router as customers_router
from .invoices import router as invoices_router
from .payments import router as payments_router
from .reconciliation import router as reconciliation_router
from .dashboard import router as dashboard_router
from .reports import router as reports_router
from .simulator import router as simulator_router
from .products import router as products_router
from .cheques import router as cheques_router

__all__ = [
    "auth_router",
    "customers_router",
    "invoices_router",
    "payments_router",
    "reconciliation_router",
    "dashboard_router",
    "reports_router",
    "simulator_router",
    "products_router",
    "cheques_router"
]
