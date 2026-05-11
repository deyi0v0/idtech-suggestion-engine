from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional
from ...db.session import get_db
from ...db.models.software import Software

router = APIRouter()

class SoftwareCreate(BaseModel):
    software_name: str

# these sample endpoints will be replaced with soft deletion
@router.get("/")
def get_all_software(db: Session = Depends(get_db)):
    try:
        stmt = select(
            Software.id,
            Software.name,
        ).order_by(Software.name)
        rows = db.execute(stmt).mappings().all()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"ERROR in get_all_software: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", status_code=201)
def add_software(payload: SoftwareCreate, db: Session = Depends(get_db)):
    try:
        software = Software(
            name=payload.software_name
        )
        db.add(software)
        db.commit()
        db.refresh(software)
        return {"id": software.id, "name": software.name}
    except Exception as e:
        db.rollback()
        print(f"ERROR in add_software: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{software_id}", status_code=200)
def delete_software(software_id: int, db: Session = Depends(get_db)):
    try:
        software = db.get(Software, software_id)
        if software is None:
            raise HTTPException(status_code=404, detail="Software not found")
        db.delete(software)
        db.commit()
        return {"deleted_id": software.id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"ERROR in delete_software: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

