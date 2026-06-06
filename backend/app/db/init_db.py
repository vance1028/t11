import uuid
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from app.core.database import Base, engine, SessionLocal
from app.models import (
    Hospital, BloodBag, BloodRequest, Dispatch, DispatchItem,
    CompatibilityMatrix, ColdChainRecord,
    BloodType, RhType, BloodComponent, BagStatus,
    UrgencyLevel, RequestStatus, DispatchStatus
)
from app.services.compatibility_service import CompatibilityService


def init_compatibility_matrix(db: Session):
    existing = db.query(CompatibilityMatrix).first()
    if existing:
        return

    for component in BloodComponent:
        for donor_bt in BloodType:
            for donor_rt in RhType:
                for recipient_bt in BloodType:
                    for recipient_rt in RhType:
                        is_emergency = True
                        compatible, is_emergency_use = CompatibilityService.is_compatible(
                            donor_bt, donor_rt, recipient_bt, recipient_rt, component, is_emergency
                        )
                        
                        if compatible:
                            priority = CompatibilityService.get_priority_score(
                                donor_bt, donor_rt, recipient_bt, recipient_rt
                            )
                            
                            matrix_item = CompatibilityMatrix(
                                donor_blood_type=donor_bt,
                                donor_rh_type=donor_rt,
                                recipient_blood_type=recipient_bt,
                                recipient_rh_type=recipient_rt,
                                component=component,
                                is_compatible=True,
                                is_emergency_only=is_emergency_use,
                                priority=priority,
                                notes=f"{donor_bt.value}{'+' if donor_rt == RhType.POSITIVE else '-'} → "
                                      f"{recipient_bt.value}{'+' if recipient_rt == RhType.POSITIVE else '-'}"
                            )
                            db.add(matrix_item)
    
    db.commit()


def init_hospitals(db: Session):
    existing = db.query(Hospital).first()
    if existing:
        return

    hospitals = [
        {
            "name": "市血液中心",
            "address": "市中心区血液路1号",
            "contact_person": "张主任",
            "contact_phone": "13800000001",
            "is_blood_center": True
        },
        {
            "name": "第一人民医院",
            "address": "东城区人民路100号",
            "contact_person": "李医生",
            "contact_phone": "13800000002",
            "is_blood_center": False
        },
        {
            "name": "第二人民医院",
            "address": "西城区建设路200号",
            "contact_person": "王医生",
            "contact_phone": "13800000003",
            "is_blood_center": False
        },
        {
            "name": "中心医院",
            "address": "南城区健康路50号",
            "contact_person": "赵医生",
            "contact_phone": "13800000004",
            "is_blood_center": False
        },
        {
            "name": "中医院",
            "address": "北城区中医大道88号",
            "contact_person": "刘医生",
            "contact_phone": "13800000005",
            "is_blood_center": False
        }
    ]

    for h in hospitals:
        hospital = Hospital(id=uuid.uuid4(), **h)
        db.add(hospital)
    
    db.commit()


def init_blood_bags(db: Session):
    existing = db.query(BloodBag).first()
    if existing:
        return

    today = date.today()
    
    def make_expiry(component, days_from_now):
        if component == BloodComponent.RBC:
            return today + timedelta(days=days_from_now if days_from_now <= 35 else 35)
        elif component == BloodComponent.PLATELET:
            return today + timedelta(days=days_from_now if days_from_now <= 5 else 5)
        elif component == BloodComponent.PLASMA:
            return today + timedelta(days=days_from_now if days_from_now <= 365 else 365)
        elif component == BloodComponent.CRYOPRECIPITATE:
            return today + timedelta(days=days_from_now if days_from_now <= 365 else 365)
        return today + timedelta(days=30)

    bag_counter = 1
    
    for component in BloodComponent:
        for bt in BloodType:
            for rt in RhType:
                for i in range(3):
                    collection_days_ago = 5 + i * 5
                    collection_date = today - timedelta(days=collection_days_ago)
                    
                    if component == BloodComponent.PLATELET and i == 0:
                        expiry_date = today + timedelta(days=1)
                    elif component == BloodComponent.PLATELET and i == 1:
                        expiry_date = today + timedelta(days=2)
                    elif component == BloodComponent.RBC and i == 0:
                        expiry_date = today + timedelta(days=7)
                    else:
                        expiry = make_expiry(component, 20 + i * 10)
                        expiry_date = expiry
                    
                    bag = BloodBag(
                        id=uuid.uuid4(),
                        bag_number=f"B{today.strftime('%Y%m%d')}{bag_counter:05d}",
                        blood_type=bt,
                        rh_type=rt,
                        component=component,
                        collection_date=collection_date,
                        expiry_date=expiry_date,
                        volume_ml=200 if component != BloodComponent.PLATELET else 50,
                        status=BagStatus.IN_STOCK,
                        location=f"冷库-{component.value}-{bt.value}",
                        notes=""
                    )
                    db.add(bag)
                    bag_counter += 1
    
    expired_platelet = BloodBag(
        id=uuid.uuid4(),
        bag_number=f"B{today.strftime('%Y%m%d')}{bag_counter:05d}",
        blood_type=BloodType.O,
        rh_type=RhType.POSITIVE,
        component=BloodComponent.PLATELET,
        collection_date=today - timedelta(days=10),
        expiry_date=today - timedelta(days=2),
        volume_ml=50,
        status=BagStatus.IN_STOCK,
        location="冷库-PLATELET-O",
        notes="已过期待报废"
    )
    db.add(expired_platelet)
    bag_counter += 1
    
    expired_rbc = BloodBag(
        id=uuid.uuid4(),
        bag_number=f"B{today.strftime('%Y%m%d')}{bag_counter:05d}",
        blood_type=BloodType.A,
        rh_type=RhType.NEGATIVE,
        component=BloodComponent.RBC,
        collection_date=today - timedelta(days=50),
        expiry_date=today - timedelta(days=15),
        volume_ml=200,
        status=BagStatus.IN_STOCK,
        location="冷库-RBC-A",
        notes="已过期待报废"
    )
    db.add(expired_rbc)
    
    db.commit()


def init_requests_and_dispatches(db: Session):
    existing = db.query(BloodRequest).first()
    if existing:
        return

    hospitals = db.query(Hospital).filter(Hospital.is_blood_center == False).all()
    if not hospitals:
        return

    today = date.today()

    request1 = BloodRequest(
        id=uuid.uuid4(),
        request_number=f"RQ{today.strftime('%Y%m%d')}00001",
        hospital_id=hospitals[0].id,
        patient_blood_type=BloodType.A,
        patient_rh_type=RhType.POSITIVE,
        component=BloodComponent.RBC,
        quantity_units=2,
        urgency=UrgencyLevel.ROUTINE,
        patient_name="张三",
        patient_age=45,
        diagnosis="贫血待查",
        status=RequestStatus.PENDING,
        requested_at=datetime.utcnow() - timedelta(hours=3),
        matched_units=0,
        notes="常规手术备血"
    )
    db.add(request1)

    request2 = BloodRequest(
        id=uuid.uuid4(),
        request_number=f"RQ{today.strftime('%Y%m%d')}00002",
        hospital_id=hospitals[1].id,
        patient_blood_type=BloodType.B,
        patient_rh_type=RhType.POSITIVE,
        component=BloodComponent.PLATELET,
        quantity_units=1,
        urgency=UrgencyLevel.URGENT,
        patient_name="李四",
        patient_age=58,
        diagnosis="化疗后血小板减少",
        status=RequestStatus.PENDING,
        requested_at=datetime.utcnow() - timedelta(hours=1),
        matched_units=0,
        notes="需要尽快输注"
    )
    db.add(request2)

    request3 = BloodRequest(
        id=uuid.uuid4(),
        request_number=f"RQ{today.strftime('%Y%m%d')}00003",
        hospital_id=hospitals[2].id,
        patient_blood_type=BloodType.O,
        patient_rh_type=RhType.POSITIVE,
        component=BloodComponent.RBC,
        quantity_units=4,
        urgency=UrgencyLevel.EMERGENCY,
        patient_name="王五",
        patient_age=32,
        diagnosis="车祸大出血",
        status=RequestStatus.PENDING,
        requested_at=datetime.utcnow() - timedelta(minutes=30),
        matched_units=0,
        notes="抢救用血，紧急！"
    )
    db.add(request3)

    hospital = hospitals[3]
    old_request = BloodRequest(
        id=uuid.uuid4(),
        request_number=f"RQ{(today - timedelta(days=1)).strftime('%Y%m%d')}00001",
        hospital_id=hospital.id,
        patient_blood_type=BloodType.AB,
        patient_rh_type=RhType.POSITIVE,
        component=BloodComponent.RBC,
        quantity_units=2,
        urgency=UrgencyLevel.URGENT,
        patient_name="赵六",
        patient_age=67,
        diagnosis="上消化道出血",
        status=RequestStatus.DISPATCHED,
        requested_at=datetime.utcnow() - timedelta(days=1),
        matched_units=2,
        notes="已完成调拨"
    )
    db.add(old_request)
    db.flush()

    suitable_bags = db.query(BloodBag).filter(
        BloodBag.blood_type.in_([BloodType.A, BloodType.AB, BloodType.O, BloodType.B]),
        BloodBag.rh_type == RhType.POSITIVE,
        BloodBag.component == BloodComponent.RBC,
        BloodBag.status == BagStatus.IN_STOCK
    ).limit(2).all()

    if suitable_bags:
        dispatch = Dispatch(
            id=uuid.uuid4(),
            dispatch_number=f"DP{(today - timedelta(days=1)).strftime('%Y%m%d')}00001",
            hospital_id=hospital.id,
            status=DispatchStatus.DELIVERED,
            total_units=2,
            dispatched_at=datetime.utcnow() - timedelta(days=1, hours=-2),
            delivered_at=datetime.utcnow() - timedelta(days=1, hours=-4),
            courier="急救中心-王师傅",
            temperature_requirement="2-6°C 冷藏运输",
            notes="上消化道出血紧急用血",
            created_at=datetime.utcnow() - timedelta(days=1),
            updated_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(dispatch)
        db.flush()

        for bag in suitable_bags:
            bag.status = BagStatus.DISPATCHED
            dispatch_item = DispatchItem(
                id=uuid.uuid4(),
                dispatch_id=dispatch.id,
                request_id=old_request.id,
                blood_bag_id=bag.id,
                is_emergency_compatibility=False,
                created_at=datetime.utcnow() - timedelta(days=1)
            )
            db.add(dispatch_item)

        cold_chain1 = ColdChainRecord(
            id=uuid.uuid4(),
            dispatch_id=dispatch.id,
            recorded_at=datetime.utcnow() - timedelta(days=1, hours=-2),
            temperature_celsius=4.2,
            location="血液中心出库",
            operator="张护士",
            notes="出库温度正常"
        )
        cold_chain2 = ColdChainRecord(
            id=uuid.uuid4(),
            dispatch_id=dispatch.id,
            recorded_at=datetime.utcnow() - timedelta(days=1, hours=-3),
            temperature_celsius=5.1,
            location="运输途中",
            operator="王师傅",
            notes="运输温度正常"
        )
        cold_chain3 = ColdChainRecord(
            id=uuid.uuid4(),
            dispatch_id=dispatch.id,
            recorded_at=datetime.utcnow() - timedelta(days=1, hours=-4),
            temperature_celsius=4.8,
            location=hospital.name + "输血科",
            operator="李护士",
            notes="已签收，温度正常"
        )
        db.add_all([cold_chain1, cold_chain2, cold_chain3])

    db.commit()


def init_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_compatibility_matrix(db)
        init_hospitals(db)
        init_blood_bags(db)
        init_requests_and_dispatches(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
    print("数据库初始化完成！")
