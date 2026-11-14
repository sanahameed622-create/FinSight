from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..dependencies import get_current_user
from ..services.simulator_service import SimulatorService

router = APIRouter(prefix="/simulator", tags=["Cash Flow Simulator"])

@router.get("/run")
def run_simulation(
    collection_efficiency_pct: float = Query(80.0, ge=10, le=100),
    average_delay_days: int = Query(15, ge=0, le=90),
    default_risk_pct: float = Query(5.0, ge=0, le=50),
    horizon_weeks: int = Query(6, ge=2, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return SimulatorService.run_cash_flow_simulation(
        db=db,
        business_id=current_user.business_id,
        collection_efficiency_pct=collection_efficiency_pct,
        average_delay_days=average_delay_days,
        default_risk_pct=default_risk_pct,
        horizon_weeks=horizon_weeks
    )
