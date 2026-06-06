import enum
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, Enum, ForeignKey, Float, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class BloodType(str, enum.Enum):
    A = "A"
    B = "B"
    AB = "AB"
    O = "O"


class RhType(str, enum.Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class BloodComponent(str, enum.Enum):
    RBC = "RBC"
    PLASMA = "PLASMA"
    PLATELET = "PLATELET"
    CRYOPRECIPITATE = "CRYOPRECIPITATE"


class BagStatus(str, enum.Enum):
    PENDING_TEST = "PENDING_TEST"
    IN_STOCK = "IN_STOCK"
    DISPATCHED = "DISPATCHED"
    SCRAPPED = "SCRAPPED"


class UrgencyLevel(str, enum.Enum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    PARTIAL_MATCHED = "PARTIAL_MATCHED"
    FULLY_MATCHED = "FULLY_MATCHED"
    DISPATCHED = "DISPATCHED"
    CANCELLED = "CANCELLED"


class DispatchStatus(str, enum.Enum):
    PREPARING = "PREPARING"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    address = Column(String(500))
    contact_person = Column(String(100))
    contact_phone = Column(String(50))
    is_blood_center = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requests = relationship("BloodRequest", back_populates="hospital")
    dispatches = relationship("Dispatch", back_populates="hospital")


class BloodBag(Base):
    __tablename__ = "blood_bags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bag_number = Column(String(50), unique=True, nullable=False)
    blood_type = Column(Enum(BloodType), nullable=False)
    rh_type = Column(Enum(RhType), nullable=False)
    component = Column(Enum(BloodComponent), nullable=False)
    collection_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    volume_ml = Column(Float, default=0)
    status = Column(Enum(BagStatus), default=BagStatus.PENDING_TEST)
    location = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dispatch_items = relationship("DispatchItem", back_populates="blood_bag")


class CompatibilityMatrix(Base):
    __tablename__ = "compatibility_matrix"

    id = Column(Integer, primary_key=True, autoincrement=True)
    donor_blood_type = Column(Enum(BloodType), nullable=False)
    donor_rh_type = Column(Enum(RhType), nullable=False)
    recipient_blood_type = Column(Enum(BloodType), nullable=False)
    recipient_rh_type = Column(Enum(RhType), nullable=False)
    component = Column(Enum(BloodComponent), nullable=False)
    is_compatible = Column(Boolean, default=False)
    is_emergency_only = Column(Boolean, default=False)
    priority = Column(Integer, default=100)
    notes = Column(String(500))

    __table_args__ = (
        UniqueConstraint('donor_blood_type', 'donor_rh_type', 'recipient_blood_type', 'recipient_rh_type', 'component', name='uq_compatibility_key'),
    )


class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_number = Column(String(50), unique=True, nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    patient_blood_type = Column(Enum(BloodType), nullable=False)
    patient_rh_type = Column(Enum(RhType), nullable=False)
    component = Column(Enum(BloodComponent), nullable=False)
    quantity_units = Column(Integer, nullable=False)
    urgency = Column(Enum(UrgencyLevel), default=UrgencyLevel.ROUTINE)
    patient_name = Column(String(100))
    patient_age = Column(Integer)
    diagnosis = Column(String(500))
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    requested_at = Column(DateTime, default=datetime.utcnow)
    matched_units = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hospital = relationship("Hospital", back_populates="requests")
    dispatch_items = relationship("DispatchItem", back_populates="request")


class Dispatch(Base):
    __tablename__ = "dispatches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispatch_number = Column(String(50), unique=True, nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    status = Column(Enum(DispatchStatus), default=DispatchStatus.PREPARING)
    total_units = Column(Integer, default=0)
    dispatched_at = Column(DateTime)
    delivered_at = Column(DateTime)
    courier = Column(String(200))
    temperature_requirement = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hospital = relationship("Hospital", back_populates="dispatches")
    items = relationship("DispatchItem", back_populates="dispatch")
    cold_chain_records = relationship("ColdChainRecord", back_populates="dispatch")


class DispatchItem(Base):
    __tablename__ = "dispatch_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispatch_id = Column(UUID(as_uuid=True), ForeignKey("dispatches.id"), nullable=False)
    request_id = Column(UUID(as_uuid=True), ForeignKey("blood_requests.id"), nullable=False)
    blood_bag_id = Column(UUID(as_uuid=True), ForeignKey("blood_bags.id"), nullable=False)
    is_emergency_compatibility = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    dispatch = relationship("Dispatch", back_populates="items")
    request = relationship("BloodRequest", back_populates="dispatch_items")
    blood_bag = relationship("BloodBag", back_populates="dispatch_items")


class ColdChainRecord(Base):
    __tablename__ = "cold_chain_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispatch_id = Column(UUID(as_uuid=True), ForeignKey("dispatches.id"), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    temperature_celsius = Column(Float, nullable=False)
    location = Column(String(500))
    operator = Column(String(100))
    notes = Column(Text)

    dispatch = relationship("Dispatch", back_populates="cold_chain_records")
