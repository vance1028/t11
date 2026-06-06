import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.models import (
    Dispatch, DispatchItem, BloodRequest, BloodBag,
    DispatchStatus, RequestStatus, BagStatus,
    ColdChainRecord,
)
from app.core.database import get_db
from app.schemas import (
    Dispatch as DispatchSchema,
    DispatchCreate,
    MatchResultItem,
    ColdChainRecord as ColdChainRecordSchema,
    ColdChainRecordCreate
)

router = APIRouter()


@router.get("/", response_model=List[DispatchSchema])
def get_dispatches(
    status: DispatchStatus = None,
    db: Session = Depends(get_db)
):
    query = db.query(Dispatch)
    
    if status:
        query = query.filter(Dispatch.status == status)
    
    return query.order_by(Dispatch.created_at.desc()).all()


@router.get("/{dispatch_id}", response_model=DispatchSchema)
def get_dispatch(dispatch_id: UUID, db: Session = Depends(get_db)):
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="调拨单不存在")
    return dispatch


@router.post("/confirm")
def confirm_dispatch(
    request_id: UUID,
    matched_items: List[MatchResultItem],
    courier: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    from app.services.inventory_service import InventoryService
    
    request = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")
    
    dispatch, error = InventoryService.confirm_dispatch(
        db, request, matched_items, request.hospital_id, courier, notes
    )
    
    if error:
        raise HTTPException(status_code=400, detail=str(error))
    
    return dispatch


@router.post("/{dispatch_id}/start-transit")
def start_transit(dispatch_id: UUID, courier: Optional[str] = None, db: Session = Depends(get_db)):
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="调拨单不存在")
    
    if dispatch.status != DispatchStatus.PREPARING:
        raise HTTPException(status_code=400, detail="调拨单状态不正确")
    
    dispatch.status = DispatchStatus.IN_TRANSIT
    dispatch.dispatched_at = datetime.utcnow()
    if courier:
        dispatch.courier = courier
    dispatch.updated_at = datetime.utcnow()
    db.commit()
    
    items = db.query(DispatchItem).filter(DispatchItem.dispatch_id == dispatch_id).all()
    for item in items:
        req = db.query(BloodRequest).filter(BloodRequest.id == item.request_id).first()
        if req and req.status != RequestStatus.DISPATCHED:
            all_matched = all(
                di.dispatch is not None and di.dispatch.status != DispatchStatus.PREPARING
                for di in req.dispatch_items
            )
            if all_matched and req.matched_units >= req.quantity_units:
                req.status = RequestStatus.DISPATCHED
                req.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "已开始运输"}


@router.post("/{dispatch_id}/confirm-delivery")
def confirm_delivery(dispatch_id: UUID, db: Session = Depends(get_db)):
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="调拨单不存在")
    
    if dispatch.status != DispatchStatus.IN_TRANSIT:
        raise HTTPException(status_code=400, detail="调拨单状态不正确")
    
    dispatch.status = DispatchStatus.DELIVERED
    dispatch.delivered_at = datetime.utcnow()
    dispatch.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "已确认送达"}


@router.get("/{dispatch_id}/cold-chain", response_model=List[ColdChainRecordSchema])
def get_cold_chain_records(dispatch_id: UUID, db: Session = Depends(get_db)):
    records = db.query(ColdChainRecord).filter(
        ColdChainRecord.dispatch_id == dispatch_id
    ).order_by(ColdChainRecord.recorded_at.desc()).all()
    return records


@router.post("/{dispatch_id}/cold-chain", response_model=ColdChainRecordSchema)
def add_cold_chain_record(
    dispatch_id: UUID,
    record: ColdChainRecordCreate,
    db: Session = Depends(get_db)
):
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="调拨单不存在")
    
    db_record = ColdChainRecord(
        id=uuid.uuid4(),
        dispatch_id=dispatch_id,
        **record.model_dump(exclude={"dispatch_id"})
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record
