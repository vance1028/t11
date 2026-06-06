import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.models import (
    BloodRequest, RequestStatus, UrgencyLevel,
)
from app.core.database import get_db
from app.schemas import (
    BloodRequest as BloodRequestSchema,
    BloodRequestCreate,
    MatchResult,
    MatchRequest
)
from app.services.allocation_service import AllocationService

router = APIRouter()


@router.get("/", response_model=List[BloodRequestSchema])
def get_requests(
    status: RequestStatus = None,
    urgency: UrgencyLevel = None,
    db: Session = Depends(get_db)
):
    query = db.query(BloodRequest)
    
    if status:
        query = query.filter(BloodRequest.status == status)
    if urgency:
        query = query.filter(BloodRequest.urgency == urgency)
    
    return query.order_by(BloodRequest.requested_at.desc()).all()


@router.get("/{request_id}", response_model=BloodRequestSchema)
def get_request(request_id: UUID, db: Session = Depends(get_db)):
    request = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")
    return request


@router.post("/", response_model=BloodRequestSchema)
def create_request(request: BloodRequestCreate, db: Session = Depends(get_db)):
    request_number = f"RQ{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
    
    db_request = BloodRequest(
        id=uuid.uuid4(),
        request_number=request_number,
        **request.model_dump()
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


@router.post("/match", response_model=MatchResult)
def match_request(match_req: MatchRequest, db: Session = Depends(get_db)):
    request = db.query(BloodRequest).filter(BloodRequest.id == match_req.request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")
    
    if request.status in [RequestStatus.FULLY_MATCHED, RequestStatus.DISPATCHED]:
        raise HTTPException(status_code=400, detail="申请已完成匹配")
    
    result = AllocationService.match_request(db, request)
    return result


@router.post("/{request_id}/cancel")
def cancel_request(request_id: UUID, db: Session = Depends(get_db)):
    request = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")
    
    if request.status in [RequestStatus.DISPATCHED]:
        raise HTTPException(status_code=400, detail="已出库的申请无法取消")
    
    request.status = RequestStatus.CANCELLED
    request.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "申请已取消"}
