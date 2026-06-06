from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models import CompatibilityMatrix, BloodType, RhType, BloodComponent
from app.core.database import get_db
from app.schemas import CompatibilityMatrixItem
from app.services.compatibility_service import CompatibilityService

router = APIRouter()


@router.get("/", response_model=List[CompatibilityMatrixItem])
def get_compatibility_matrix(
    component: BloodComponent = None,
    db: Session = Depends(get_db)
):
    query = db.query(CompatibilityMatrix)
    if component:
        query = query.filter(CompatibilityMatrix.component == component)
    
    return query.order_by(
        CompatibilityMatrix.donor_blood_type,
        CompatibilityMatrix.donor_rh_type,
        CompatibilityMatrix.priority
    ).all()


@router.get("/check")
def check_compatibility(
    donor_blood_type: BloodType,
    donor_rh_type: RhType,
    recipient_blood_type: BloodType,
    recipient_rh_type: RhType,
    component: BloodComponent,
    is_emergency: bool = False
):
    compatible, is_emergency_use = CompatibilityService.is_compatible(
        donor_blood_type,
        donor_rh_type,
        recipient_blood_type,
        recipient_rh_type,
        component,
        is_emergency
    )
    
    priority = CompatibilityService.get_priority_score(
        donor_blood_type,
        donor_rh_type,
        recipient_blood_type,
        recipient_rh_type
    )
    
    return {
        "donor_blood_type": donor_blood_type,
        "donor_rh_type": donor_rh_type,
        "recipient_blood_type": recipient_blood_type,
        "recipient_rh_type": recipient_rh_type,
        "component": component,
        "is_compatible": compatible,
        "is_emergency_use": is_emergency_use,
        "priority_score": priority
    }


@router.get("/compatible-donors")
def get_compatible_donors(
    recipient_blood_type: BloodType,
    recipient_rh_type: RhType,
    component: BloodComponent,
    is_emergency: bool = False
):
    compatible = CompatibilityService.get_compatible_blood_types(
        recipient_blood_type,
        recipient_rh_type,
        component,
        is_emergency
    )
    
    result = []
    for bt, rt, is_emergency_use in compatible:
        priority = CompatibilityService.get_priority_score(
            bt, rt, recipient_blood_type, recipient_rh_type
        )
        result.append({
            "blood_type": bt,
            "rh_type": rt,
            "is_emergency_use": is_emergency_use,
            "priority_score": priority
        })
    
    return sorted(result, key=lambda x: (-x["priority_score"], x["is_emergency_use"]))
