from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import (
    BloodBag, BloodRequest, Dispatch,
    BagStatus, RequestStatus, DispatchStatus,
    UrgencyLevel, BloodComponent,
)
from app.core.database import get_db
from app.schemas import DashboardStats, InventoryStats
from app.services.allocation_service import AllocationService

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    today = date.today()
    
    total_inventory = db.query(func.count(BloodBag.id)).filter(
        BloodBag.status == BagStatus.IN_STOCK
    ).scalar() or 0
    
    total_requests_pending = db.query(func.count(BloodRequest.id)).filter(
        BloodRequest.status.in_([RequestStatus.PENDING, RequestStatus.PARTIAL_MATCHED])
    ).scalar() or 0
    
    total_dispatches_in_transit = db.query(func.count(Dispatch.id)).filter(
        Dispatch.status == DispatchStatus.IN_TRANSIT
    ).scalar() or 0
    
    expiring_soon_count = 0
    expired_count = 0
    
    for component in BloodComponent:
        warning_days = AllocationService.get_warning_days(component)
        warning_deadline = today + timedelta(days=warning_days)
        
        expiring_soon_count += db.query(func.count(BloodBag.id)).filter(
            and_(
                BloodBag.status == BagStatus.IN_STOCK,
                BloodBag.component == component,
                BloodBag.expiry_date >= today,
                BloodBag.expiry_date <= warning_deadline
            )
        ).scalar() or 0
        
        expired_count += db.query(func.count(BloodBag.id)).filter(
            and_(
                BloodBag.status == BagStatus.IN_STOCK,
                BloodBag.component == component,
                BloodBag.expiry_date < today
            )
        ).scalar() or 0
    
    inventory_by_type = AllocationService.get_inventory_stats(db)
    
    urgent_requests = db.query(BloodRequest).filter(
        BloodRequest.status.in_([RequestStatus.PENDING, RequestStatus.PARTIAL_MATCHED]),
        BloodRequest.urgency.in_([UrgencyLevel.URGENT, UrgencyLevel.EMERGENCY])
    ).order_by(BloodRequest.urgency.desc(), BloodRequest.requested_at.asc()).all()
    
    return DashboardStats(
        total_inventory=total_inventory,
        total_requests_pending=total_requests_pending,
        total_dispatches_in_transit=total_dispatches_in_transit,
        expiring_soon_count=expiring_soon_count,
        expired_count=expired_count,
        inventory_by_type=inventory_by_type,
        urgent_requests=urgent_requests
    )
