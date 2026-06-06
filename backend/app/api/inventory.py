from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from uuid import UUID
from datetime import date, timedelta

from app.models import BloodBag, BagStatus, BloodType, RhType, BloodComponent
from app.core.database import get_db
from app.schemas import BloodBag as BloodBagSchema, BloodBagCreate, BloodBagWithExpiryInfo
from app.services.allocation_service import AllocationService

router = APIRouter()


@router.get("/", response_model=List[BloodBagWithExpiryInfo])
def get_blood_bags(
    blood_type: Optional[BloodType] = None,
    rh_type: Optional[RhType] = None,
    component: Optional[BloodComponent] = None,
    status: Optional[BagStatus] = None,
    only_in_stock: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(BloodBag)
    
    filters = []
    if blood_type:
        filters.append(BloodBag.blood_type == blood_type)
    if rh_type:
        filters.append(BloodBag.rh_type == rh_type)
    if component:
        filters.append(BloodBag.component == component)
    if status:
        filters.append(BloodBag.status == status)
    if only_in_stock:
        filters.append(BloodBag.status == BagStatus.IN_STOCK)
    
    if filters:
        query = query.filter(and_(*filters))
    
    bags = query.order_by(BloodBag.expiry_date.asc()).all()
    
    result = []
    for bag in bags:
        days_to_expiry = AllocationService.calculate_days_to_expiry(bag.expiry_date)
        bag_dict = {c.name: getattr(bag, c.name) for c in bag.__table__.columns}
        bag_dict['days_to_expiry'] = days_to_expiry
        result.append(bag_dict)
    
    return result


@router.get("/{bag_id}", response_model=BloodBagWithExpiryInfo)
def get_blood_bag(bag_id: UUID, db: Session = Depends(get_db)):
    bag = db.query(BloodBag).filter(BloodBag.id == bag_id).first()
    if not bag:
        raise HTTPException(status_code=404, detail="血袋不存在")
    
    days_to_expiry = AllocationService.calculate_days_to_expiry(bag.expiry_date)
    bag_dict = {c.name: getattr(bag, c.name) for c in bag.__table__.columns}
    bag_dict['days_to_expiry'] = days_to_expiry
    return bag_dict


@router.post("/", response_model=BloodBagSchema)
def create_blood_bag(bag: BloodBagCreate, db: Session = Depends(get_db)):
    existing = db.query(BloodBag).filter(BloodBag.bag_number == bag.bag_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="血袋编号已存在")
    
    db_bag = BloodBag(**bag.model_dump())
    db.add(db_bag)
    db.commit()
    db.refresh(db_bag)
    return db_bag


@router.post("/{bag_id}/scrap")
def scrap_blood_bag(bag_id: UUID, reason: str, db: Session = Depends(get_db)):
    from app.services.inventory_service import InventoryService
    
    success, error = InventoryService.mark_bag_scrapped(db, bag_id, reason)
    if not success:
        raise HTTPException(status_code=400, detail=str(error))
    return {"message": "血袋已报废"}


@router.get("/alerts/expiring-soon")
def get_expiring_soon(db: Session = Depends(get_db)):
    today = date.today()
    alerts = []
    
    for component in BloodComponent:
        warning_days = AllocationService.get_warning_days(component)
        warning_deadline = today + timedelta(days=warning_days)
        
        bags = db.query(BloodBag).filter(
            and_(
                BloodBag.status == BagStatus.IN_STOCK,
                BloodBag.component == component,
                BloodBag.expiry_date >= today,
                BloodBag.expiry_date <= warning_deadline
            )
        ).order_by(BloodBag.expiry_date.asc()).all()
        
        for bag in bags:
            days_to_expiry = AllocationService.calculate_days_to_expiry(bag.expiry_date)
            alerts.append({
                "bag_id": str(bag.id),
                "bag_number": bag.bag_number,
                "blood_type": bag.blood_type,
                "rh_type": bag.rh_type,
                "component": bag.component,
                "expiry_date": bag.expiry_date.isoformat(),
                "days_to_expiry": days_to_expiry,
                "warning_days": warning_days,
                "level": "critical" if days_to_expiry <= 1 else "warning"
            })
    
    return alerts


@router.get("/alerts/expired")
def get_expired(db: Session = Depends(get_db)):
    today = date.today()
    
    bags = db.query(BloodBag).filter(
        and_(
            BloodBag.status == BagStatus.IN_STOCK,
            BloodBag.expiry_date < today
        )
    ).order_by(BloodBag.expiry_date.asc()).all()
    
    result = []
    for bag in bags:
        days_to_expiry = AllocationService.calculate_days_to_expiry(bag.expiry_date)
        result.append({
            "bag_id": str(bag.id),
            "bag_number": bag.bag_number,
            "blood_type": bag.blood_type,
            "rh_type": bag.rh_type,
            "component": bag.component,
            "expiry_date": bag.expiry_date.isoformat(),
            "days_overdue": abs(days_to_expiry)
        })
    
    return result
