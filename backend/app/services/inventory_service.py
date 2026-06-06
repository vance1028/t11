import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError

from app.models import (
    BloodBag, BloodRequest, Dispatch, DispatchItem,
    BagStatus, RequestStatus, DispatchStatus
)
from app.services.allocation_service import AllocationService
from app.schemas import MatchResultItem


class InventoryService:
    
    @staticmethod
    def lock_and_allocate_bags(
        db: Session,
        request: BloodRequest,
        matched_items: List[MatchResultItem]
    ) -> tuple[List[DispatchItem], Optional[Exception]]:
        """
        并发安全地分配血袋。
        使用 SELECT FOR UPDATE 行锁一次性锁定所有匹配的血袋，确保同一袋血不会被两个并发请求同时分配。
        """
        allocated_items = []
        try:
            bag_ids = [item.blood_bag_id for item in matched_items]
            
            if not bag_ids:
                return None, Exception("没有需要分配的血袋")
            
            stmt = (
                select(BloodBag)
                .where(
                    and_(
                        BloodBag.id.in_(bag_ids),
                        BloodBag.status == BagStatus.IN_STOCK
                    )
                )
                .with_for_update(skip_locked=False)
            )
            
            result = db.execute(stmt)
            bags = result.scalars().all()
            
            if len(bags) != len(matched_items):
                db.rollback()
                locked_ids = {bag.id for bag in bags}
                missing = [item.bag_number for item in matched_items if item.blood_bag_id not in locked_ids]
                return None, Exception(f"血袋 {', '.join(missing)} 已被其他请求分配，请重新匹配")
            
            bag_map = {bag.id: bag for bag in bags}
            
            for item in matched_items:
                bag = bag_map.get(item.blood_bag_id)
                if not bag:
                    db.rollback()
                    return None, Exception(f"血袋 {item.bag_number} 不存在")
                
                bag.status = BagStatus.DISPATCHED
                bag.updated_at = datetime.utcnow()
                
                dispatch_item = DispatchItem(
                    id=uuid.uuid4(),
                    request_id=request.id,
                    blood_bag_id=bag.id,
                    is_emergency_compatibility=item.is_emergency_compatibility,
                    created_at=datetime.utcnow()
                )
                allocated_items.append(dispatch_item)
            
            return allocated_items, None
            
        except SQLAlchemyError as e:
            db.rollback()
            return None, e

    @staticmethod
    def confirm_dispatch(
        db: Session,
        request: BloodRequest,
        matched_items: List[MatchResultItem],
        hospital_id,
        courier: Optional[str] = None,
        notes: Optional[str] = None
    ) -> tuple[Optional[Dispatch], Optional[Exception]]:
        """
        创建调拨单并扣减库存。
        整个操作在一个事务中完成，确保原子性。
        """
        try:
            dispatch_items, error = InventoryService.lock_and_allocate_bags(
                db, request, matched_items
            )
            
            if error:
                return None, error
            
            if not dispatch_items:
                return None, Exception("没有可分配的血袋")
            
            dispatch_number = f"DP{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
            
            dispatch = Dispatch(
                id=uuid.uuid4(),
                dispatch_number=dispatch_number,
                hospital_id=hospital_id,
                status=DispatchStatus.PREPARING,
                total_units=len(dispatch_items),
                courier=courier,
                temperature_requirement=InventoryService._get_temp_requirement(request.component),
                notes=notes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(dispatch)
            db.flush()
            
            for item in dispatch_items:
                item.dispatch_id = dispatch.id
                db.add(item)
            
            request.matched_units += len(dispatch_items)
            if request.matched_units >= request.quantity_units:
                request.status = RequestStatus.FULLY_MATCHED
            else:
                request.status = RequestStatus.PARTIAL_MATCHED
            
            request.updated_at = datetime.utcnow()
            
            db.commit()
            
            dispatch.items = dispatch_items
            
            return dispatch, None
            
        except Exception as e:
            db.rollback()
            return None, e

    @staticmethod
    def _get_temp_requirement(component) -> str:
        from app.models import BloodComponent
        if component == BloodComponent.RBC:
            return "2-6°C 冷藏运输"
        elif component == BloodComponent.PLATELET:
            return "20-24°C 常温振荡运输"
        elif component == BloodComponent.PLASMA:
            return "-18°C 以下冷冻运输"
        elif component == BloodComponent.CRYOPRECIPITATE:
            return "-18°C 以下冷冻运输"
        return "按标准冷链运输"

    @staticmethod
    def release_bag(db: Session, bag_id) -> tuple[bool, Optional[Exception]]:
        """
        释放已分配但未出库的血袋（取消分配时使用）
        """
        try:
            stmt = (
                select(BloodBag)
                .where(BloodBag.id == bag_id)
                .with_for_update()
            )
            result = db.execute(stmt)
            bag = result.scalar_one_or_none()
            
            if not bag:
                return False, Exception("血袋不存在")
            
            if bag.status != BagStatus.DISPATCHED:
                return False, Exception(f"血袋当前状态为 {bag.status}，无法释放")
            
            bag.status = BagStatus.IN_STOCK
            bag.updated_at = datetime.utcnow()
            db.commit()
            
            return True, None
            
        except Exception as e:
            db.rollback()
            return False, e

    @staticmethod
    def mark_bag_scrapped(db: Session, bag_id, reason: str) -> tuple[bool, Optional[Exception]]:
        """
        标记血袋为报废
        """
        try:
            stmt = (
                select(BloodBag)
                .where(BloodBag.id == bag_id)
                .with_for_update()
            )
            result = db.execute(stmt)
            bag = result.scalar_one_or_none()
            
            if not bag:
                return False, Exception("血袋不存在")
            
            if bag.status == BagStatus.DISPATCHED:
                return False, Exception("血袋已出库，无法报废")
            
            bag.status = BagStatus.SCRAPPED
            bag.notes = (bag.notes or "") + f"\n报废原因: {reason}"
            bag.updated_at = datetime.utcnow()
            db.commit()
            
            return True, None
            
        except Exception as e:
            db.rollback()
            return False, e
