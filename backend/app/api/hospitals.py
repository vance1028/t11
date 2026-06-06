from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.models import Hospital
from app.core.database import get_db
from app.schemas import Hospital as HospitalSchema, HospitalCreate

router = APIRouter()


@router.get("/", response_model=List[HospitalSchema])
def get_hospitals(db: Session = Depends(get_db)):
    hospitals = db.query(Hospital).order_by(Hospital.name).all()
    return hospitals


@router.get("/{hospital_id}", response_model=HospitalSchema)
def get_hospital(hospital_id: UUID, db: Session = Depends(get_db)):
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="医院不存在")
    return hospital


@router.post("/", response_model=HospitalSchema)
def create_hospital(hospital: HospitalCreate, db: Session = Depends(get_db)):
    db_hospital = Hospital(**hospital.model_dump())
    db.add(db_hospital)
    db.commit()
    db.refresh(db_hospital)
    return db_hospital
