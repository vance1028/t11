import threading
import time
import requests
from datetime import datetime, timedelta
import uuid

BASE_URL = "http://localhost:8472/api/v1"

def create_test_hospital(name):
    """创建测试医院"""
    r = requests.post(f"{BASE_URL}/hospitals/", json={
        "name": name,
        "address": f"测试地址-{name}",
        "contact_person": "测试医生",
        "contact_phone": "13800000000"
    })
    return r.json()

def create_test_request(hospital_id, blood_type, rh_type, component, quantity=1):
    """创建测试申请"""
    r = requests.post(f"{BASE_URL}/requests/", json={
        "hospital_id": str(hospital_id),
        "patient_blood_type": blood_type,
        "patient_rh_type": rh_type,
        "component": component,
        "quantity_units": quantity,
        "urgency": "ROUTINE",
        "patient_name": "测试患者",
        "patient_age": 30,
        "diagnosis": "测试诊断"
    })
    return r.json()

def match_and_allocate(request_id):
    """匹配并分配"""
    # 先匹配
    r = requests.post(f"{BASE_URL}/requests/match", json={
        "request_id": str(request_id)
    })
    if r.status_code != 200:
        print(f"匹配失败: {r.status_code} {r.text}")
        return None
    match_result = r.json()
    print(f"匹配结果: {match_result['total_matched']} 袋")
    for item in match_result['matched_items']:
        print(f"  - {item['bag_number']}: {item['blood_type']}{item['rh_type']}, {item['days_to_expiry']}天后到期")
    
    if match_result['total_matched'] == 0:
        return None
    
    # 确认调拨
    time.sleep(0.5)  # 模拟用户思考时间
    r = requests.post(f"{BASE_URL}/dispatches/confirm", params={
        "request_id": str(request_id)
    }, json=match_result['matched_items'])
    
    if r.status_code == 200:
        dispatch = r.json()
        print(f"调拨成功: {dispatch['dispatch_number']}")
        return dispatch
    else:
        print(f"调拨失败: {r.status_code} {r.text}")
        return None

def test_concurrent_allocation():
    """测试并发分配"""
    print("=" * 60)
    print("测试并发分配问题")
    print("=" * 60)
    
    # 创建两家医院
    hospital1 = create_test_hospital("并发测试医院1")
    hospital2 = create_test_hospital("并发测试医院2")
    print(f"医院1: {hospital1['id']}")
    print(f"医院2: {hospital2['id']}")
    
    # 创建两个申请，都是A型Rh阳性红细胞，各要1袋
    request1 = create_test_request(hospital1['id'], "A", "POSITIVE", "RBC", 1)
    request2 = create_test_request(hospital2['id'], "A", "POSITIVE", "RBC", 1)
    print(f"申请1: {request1['id']}")
    print(f"申请2: {request2['id']}")
    
    # 并发执行匹配和分配
    results = [None, None]
    
    def worker(request_id, index):
        results[index] = match_and_allocate(request_id)
    
    t1 = threading.Thread(target=worker, args=(request1['id'], 0))
    t2 = threading.Thread(target=worker, args=(request2['id'], 1))
    
    print("\n开始并发执行...")
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    print("\n" + "=" * 60)
    print("结果汇总:")
    print("=" * 60)
    success_count = sum(1 for r in results if r is not None)
    print(f"成功调拨数: {success_count}")
    
    if success_count == 2:
        # 检查是否分配了同一袋血
        bags1 = {item['blood_bag_id'] for item in results[0]['items']}
        bags2 = {item['blood_bag_id'] for item in results[1]['items']}
        overlap = bags1.intersection(bags2)
        if overlap:
            print(f"❌ 严重问题！同一袋血被分配给两家医院: {overlap}")
        else:
            print(f"✅ 正常，没有重复分配")
    elif success_count == 1:
        print(f"⚠️  只有一家成功，另一家被正确阻止")
    else:
        print(f"❌ 两家都失败了")

if __name__ == "__main__":
    test_concurrent_allocation()
