from datetime import datetime, date, timedelta
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models import (
    BloodBag, BloodRequest, BagStatus, BloodComponent,
    UrgencyLevel, BloodType, RhType
)
from app.services.compatibility_service import CompatibilityService
from app.schemas import MatchResult, MatchResultItem


class AllocationService:
    
    RBC_EXPIRY_WARNING_DAYS = 14
    PLATELET_EXPIRY_WARNING_DAYS = 3
    PLASMA_EXPIRY_WARNING_DAYS = 30
    CRYOPRECIPITATE_EXPIRY_WARNING_DAYS = 30

    @staticmethod
    def get_warning_days(component: BloodComponent) -> int:
        if component == BloodComponent.RBC:
            return AllocationService.RBC_EXPIRY_WARNING_DAYS
        elif component == BloodComponent.PLATELET:
            return AllocationService.PLATELET_EXPIRY_WARNING_DAYS
        elif component == BloodComponent.PLASMA:
            return AllocationService.PLASMA_EXPIRY_WARNING_DAYS
        elif component == BloodComponent.CRYOPRECIPITATE:
            return AllocationService.CRYOPRECIPITATE_EXPIRY_WARNING_DAYS
        return 7

    @staticmethod
    def calculate_days_to_expiry(expiry_date: date) -> int:
        today = date.today()
        delta = expiry_date - today
        return delta.days

    @staticmethod
    def find_matching_bags(
        db: Session,
        request: BloodRequest,
        exclude_bag_ids: List = None
    ) -> List[Tuple[BloodBag, bool]]:
        if exclude_bag_ids is None:
            exclude_bag_ids = []

        is_emergency = request.urgency in [UrgencyLevel.URGENT, UrgencyLevel.EMERGENCY]
        
        compatible_types = CompatibilityService.get_compatible_blood_types(
            request.patient_blood_type,
            request.patient_rh_type,
            request.component,
            is_emergency
        )

        if not compatible_types:
            return []

        compatible_conditions = []
        for bt, rt, _ in compatible_types:
            compatible_conditions.append(
                and_(
                    BloodBag.blood_type == bt,
                    BloodBag.rh_type == rt
                )
            )

        query = db.query(BloodBag).filter(
            and_(
                BloodBag.status == BagStatus.IN_STOCK,
                BloodBag.component == request.component,
                BloodBag.expiry_date >= date.today(),
                or_(*compatible_conditions)
            )
        )

        if exclude_bag_ids:
            query = query.filter(BloodBag.id.notin_(exclude_bag_ids))

        query = query.order_by(BloodBag.expiry_date.asc(), BloodBag.collection_date.asc())

        bags = query.all()

        results = []
        for bag in bags:
            compatible, is_emergency_use = CompatibilityService.is_compatible(
                bag.blood_type,
                bag.rh_type,
                request.patient_blood_type,
                request.patient_rh_type,
                request.component,
                is_emergency
            )
            if compatible:
                results.append((bag, is_emergency_use))

        return results

    @staticmethod
    def sort_bags_by_priority(
        bags_with_emergency: List[Tuple[BloodBag, bool]],
        request: BloodRequest
    ) -> List[Tuple[BloodBag, bool]]:
        def sort_key(item):
            bag, is_emergency_use = item
            days_to_expiry = AllocationService.calculate_days_to_expiry(bag.expiry_date)
            
            abo_match = bag.blood_type == request.patient_blood_type
            rh_match = bag.rh_type == request.patient_rh_type
            
            match_tier = 0
            if abo_match and rh_match:
                match_tier = 0
            elif abo_match and not rh_match:
                match_tier = 1
            elif not abo_match and rh_match:
                match_tier = 2
            else:
                match_tier = 3
            
            emergency_penalty = 1 if is_emergency_use else 0
            
            return (
                emergency_penalty,
                match_tier,
                days_to_expiry,
                bag.collection_date
            )

        return sorted(bags_with_emergency, key=sort_key)

    @staticmethod
    def match_request(
        db: Session,
        request: BloodRequest,
        exclude_bag_ids: List = None
    ) -> MatchResult:
        remaining = request.quantity_units - request.matched_units
        
        if remaining <= 0:
            return MatchResult(
                request_id=request.id,
                request_number=request.request_number,
                matched_items=[],
                total_matched=0,
                quantity_needed=request.quantity_units,
                is_fully_matched=True
            )

        matching_bags = AllocationService.find_matching_bags(db, request, exclude_bag_ids)
        
        if not matching_bags:
            return MatchResult(
                request_id=request.id,
                request_number=request.request_number,
                matched_items=[],
                total_matched=0,
                quantity_needed=remaining,
                is_fully_matched=False
            )

        sorted_bags = AllocationService.sort_bags_by_priority(matching_bags, request)
        
        matched_items = []
        total_matched = 0

        for bag, is_emergency_use in sorted_bags:
            if total_matched >= remaining:
                break
            
            days_to_expiry = AllocationService.calculate_days_to_expiry(bag.expiry_date)
            
            matched_items.append(MatchResultItem(
                blood_bag_id=bag.id,
                bag_number=bag.bag_number,
                blood_type=bag.blood_type,
                rh_type=bag.rh_type,
                component=bag.component,
                expiry_date=bag.expiry_date,
                days_to_expiry=days_to_expiry,
                is_emergency_compatibility=is_emergency_use
            ))
            total_matched += 1

        return MatchResult(
            request_id=request.id,
            request_number=request.request_number,
            matched_items=matched_items,
            total_matched=total_matched,
            quantity_needed=remaining,
            is_fully_matched=total_matched >= remaining
        )

    @staticmethod
    def get_inventory_stats(db: Session) -> List:
        from app.schemas import InventoryStats
        
        results = []
        for component in BloodComponent:
            for bt in BloodType:
                for rt in RhType:
                    warning_days = AllocationService.get_warning_days(component)
                    today = date.today()
                    
                    total = db.query(func.count(BloodBag.id)).filter(
                        and_(
                            BloodBag.status == BagStatus.IN_STOCK,
                            BloodBag.blood_type == bt,
                            BloodBag.rh_type == rt,
                            BloodBag.component == component
                        )
                    ).scalar() or 0
                    
                    if total == 0:
                        continue
                    
                    warning_deadline = today + timedelta(days=warning_days)
                    expiring_soon = db.query(func.count(BloodBag.id)).filter(
                        and_(
                            BloodBag.status == BagStatus.IN_STOCK,
                            BloodBag.blood_type == bt,
                            BloodBag.rh_type == rt,
                            BloodBag.component == component,
                            BloodBag.expiry_date >= today,
                            BloodBag.expiry_date <= warning_deadline
                        )
                    ).scalar() or 0
                    
                    expired = db.query(func.count(BloodBag.id)).filter(
                        and_(
                            BloodBag.status == BagStatus.IN_STOCK,
                            BloodBag.blood_type == bt,
                            BloodBag.rh_type == rt,
                            BloodBag.component == component,
                            BloodBag.expiry_date < today
                        )
                    ).scalar() or 0
                    
                    results.append(InventoryStats(
                        blood_type=bt,
                        rh_type=rt,
                        component=component,
                        total_units=total,
                        expiring_soon=expiring_soon,
                        expired=expired
                    ))
        
        return results
