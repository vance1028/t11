from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models import (
    BloodType, RhType, BloodComponent, BagStatus,
    UrgencyLevel, RequestStatus, DispatchStatus
)


class HospitalBase(BaseModel):
    name: str
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    is_blood_center: bool = False


class HospitalCreate(HospitalBase):
    pass


class Hospital(HospitalBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BloodBagBase(BaseModel):
    bag_number: str
    blood_type: BloodType
    rh_type: RhType
    component: BloodComponent
    collection_date: date
    expiry_date: date
    volume_ml: float = 0
    status: BagStatus = BagStatus.PENDING_TEST
    location: Optional[str] = None
    notes: Optional[str] = None


class BloodBagCreate(BloodBagBase):
    pass


class BloodBag(BloodBagBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BloodBagWithExpiryInfo(BloodBag):
    days_to_expiry: int


class BloodRequestBase(BaseModel):
    hospital_id: UUID
    patient_blood_type: BloodType
    patient_rh_type: RhType
    component: BloodComponent
    quantity_units: int
    urgency: UrgencyLevel = UrgencyLevel.ROUTINE
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None


class BloodRequestCreate(BloodRequestBase):
    pass


class BloodRequest(BloodRequestBase):
    id: UUID
    request_number: str
    status: RequestStatus
    requested_at: datetime
    matched_units: int
    created_at: datetime
    updated_at: datetime
    hospital: Optional[Hospital] = None

    class Config:
        from_attributes = True


class DispatchItemBase(BaseModel):
    dispatch_id: UUID
    request_id: UUID
    blood_bag_id: UUID
    is_emergency_compatibility: bool = False


class DispatchItemCreate(DispatchItemBase):
    pass


class DispatchItem(DispatchItemBase):
    id: UUID
    created_at: datetime
    blood_bag: Optional[BloodBag] = None

    class Config:
        from_attributes = True


class DispatchBase(BaseModel):
    hospital_id: UUID
    status: DispatchStatus = DispatchStatus.PREPARING
    courier: Optional[str] = None
    temperature_requirement: Optional[str] = None
    notes: Optional[str] = None


class DispatchCreate(DispatchBase):
    pass


class Dispatch(DispatchBase):
    id: UUID
    dispatch_number: str
    total_units: int
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    hospital: Optional[Hospital] = None
    items: List[DispatchItem] = []

    class Config:
        from_attributes = True


class MatchRequest(BaseModel):
    request_id: UUID


class MatchResultItem(BaseModel):
    blood_bag_id: UUID
    bag_number: str
    blood_type: BloodType
    rh_type: RhType
    component: BloodComponent
    expiry_date: date
    days_to_expiry: int
    is_emergency_compatibility: bool


class MatchResult(BaseModel):
    request_id: UUID
    request_number: str
    matched_items: List[MatchResultItem]
    total_matched: int
    quantity_needed: int
    is_fully_matched: bool


class InventoryStats(BaseModel):
    blood_type: BloodType
    rh_type: RhType
    component: BloodComponent
    total_units: int
    expiring_soon: int
    expired: int


class DashboardStats(BaseModel):
    total_inventory: int
    total_requests_pending: int
    total_dispatches_in_transit: int
    expiring_soon_count: int
    expired_count: int
    inventory_by_type: List[InventoryStats]
    urgent_requests: List[BloodRequest]


class CompatibilityMatrixItem(BaseModel):
    donor_blood_type: BloodType
    donor_rh_type: RhType
    recipient_blood_type: BloodType
    recipient_rh_type: RhType
    component: BloodComponent
    is_compatible: bool
    is_emergency_only: bool
    priority: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ColdChainRecordBase(BaseModel):
    dispatch_id: UUID
    temperature_celsius: float
    location: Optional[str] = None
    operator: Optional[str] = None
    notes: Optional[str] = None


class ColdChainRecordCreate(ColdChainRecordBase):
    pass


class ColdChainRecord(ColdChainRecordBase):
    id: UUID
    recorded_at: datetime

    class Config:
        from_attributes = True
