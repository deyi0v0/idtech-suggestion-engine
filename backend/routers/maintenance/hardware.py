from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional
from ...db.session import get_db
from ...db.models.hardware import Hardware

router = APIRouter()

class HardwareCreate(BaseModel):
    model_name: str
    operate_temperature: Optional[str] = None
    input_power: Optional[str] = None
    ip_rating: Optional[str] = None
    ik_rating: Optional[str] = None
    interface: Optional[str] = None

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

@router.post("/", status_code=201)
def add_hardware(payload: HardwareCreate, db: Session = Depends(get_db)):
    try:
        device = Hardware(
            model_name=payload.model_name,
            operate_temperature=payload.operate_temperature or None,
            input_power=payload.input_power or None,
            ip_rating=payload.ip_rating or None,
            ik_rating=payload.ik_rating or None,
            interface=payload.interface or None,
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        return {"id": device.id, "model_name": device.model_name}
    except Exception as e:
        db.rollback()
        print(f"ERROR in add_hardware: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{device_id}", status_code=200)
def delete_hardware(device_id: int, db: Session = Depends(get_db)):
    try:
        device = db.get(Hardware, device_id)
        if device is None:
            raise HTTPException(status_code=404, detail="Device not found")
        db.delete(device)
        db.commit()
        return {"deleted_id": device_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"ERROR in delete_hardware: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
