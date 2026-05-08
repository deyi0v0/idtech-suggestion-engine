from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...db.models.hardware import Hardware

router = APIRouter()

@router.get("/")
def get_all_hardware(db: Session = Depends(get_db)):
    try:
        stmt = select(
            Hardware.id,
            Hardware.model_name,
            Hardware.operate_temperature,
            Hardware.input_power,
            Hardware.ip_rating,
            Hardware.ik_rating,
            Hardware.interface,
        ).order_by(Hardware.model_name)
        rows = db.execute(stmt).mappings().all()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"ERROR in get_all_hardware: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
