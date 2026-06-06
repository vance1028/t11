import requests
from datetime import datetime, timedelta
import uuid

BASE_URL = "http://localhost:8472/api/v1"

def test_rh_matching():
    """测试Rh血型匹配：常规申请不能跨Rh类型"""
    print("=" * 60)
    print("测试1: Rh血型匹配（常规申请不能跨Rh类型）")
    print("=" * 60)
    
    # 先获取一家医院
    r = requests.get(f"{BASE_URL}/hospitals/")
    hospitals = r.json()
    hospital_id = hospitals[0]['id']
    print(f"使用医院: {hospitals[0]['name']}")
    
    # 创建A型Rh阳性患者的常规申请
    r = requests.post(f"{BASE_URL}/requests/", json={
        "hospital_id": str(hospital_id),
        "patient_blood_type": "A",
        "patient_rh_type": "POSITIVE",
        "component": "RBC",
        "quantity_units": 10,
        "urgency": "ROUTINE",
        "patient_name": "Rh匹配测试患者",
        "patient_age": 30,
        "diagnosis": "测试诊断"
    })
    request = r.json()
    print(f"创建申请: {request['id']} (A型Rh阳性, 常规)")
    
    # 匹配
    r = requests.post(f"{BASE_URL}/requests/match", json={
        "request_id": str(request['id'])
    })
    match_result = r.json()
    
    print(f"\n匹配到 {match_result['total_matched']} 袋:")
    has_rh_negative = False
    for item in match_result['matched_items']:
        print(f"  - {item['bag_number']}: {item['blood_type']}{item['rh_type']}, "
              f"{item['days_to_expiry']}天后到期, "
              f"{'紧急代偿' if item['is_emergency_compatibility'] else '同型'}")
        if item['rh_type'] == 'NEGATIVE':
            has_rh_negative = True
    
    if has_rh_negative:
        print("\n❌ 失败！常规申请匹配到了Rh阴性的血袋")
    else:
        print("\n✅ 成功！常规申请只匹配到了Rh阳性的血袋")
    
    return not has_rh_negative

def test_fifo_sorting():
    """测试FIFO排序：临期血袋应该排在前面"""
    print("\n" + "=" * 60)
    print("测试2: FIFO排序（临期血袋优先）")
    print("=" * 60)
    
    # 先获取一家医院
    r = requests.get(f"{BASE_URL}/hospitals/")
    hospitals = r.json()
    hospital_id = hospitals[0]['id']
    
    # 创建A型Rh阳性患者的申请
    r = requests.post(f"{BASE_URL}/requests/", json={
        "hospital_id": str(hospital_id),
        "patient_blood_type": "A",
        "patient_rh_type": "POSITIVE",
        "component": "RBC",
        "quantity_units": 10,
        "urgency": "ROUTINE",
        "patient_name": "FIFO测试患者",
        "patient_age": 30,
        "diagnosis": "测试诊断"
    })
    request = r.json()
    
    # 匹配
    r = requests.post(f"{BASE_URL}/requests/match", json={
        "request_id": str(request['id'])
    })
    match_result = r.json()
    
    print(f"匹配到 {match_result['total_matched']} 袋:")
    days_list = []
    for i, item in enumerate(match_result['matched_items']):
        print(f"  #{i+1}: {item['bag_number']}: {item['blood_type']}{item['rh_type']}, "
              f"{item['days_to_expiry']}天后到期")
        days_list.append(item['days_to_expiry'])
    
    # 检查是否按有效期升序排列
    is_sorted = all(days_list[i] <= days_list[i+1] for i in range(len(days_list)-1))
    
    if is_sorted:
        print("\n✅ 成功！血袋按有效期升序排列（临期优先）")
    else:
        print("\n❌ 失败！血袋没有按有效期升序排列")
        print(f"  有效期序列: {days_list}")
    
    return is_sorted

def test_concurrent_allocation():
    """测试并发分配（简化版）"""
    print("\n" + "=" * 60)
    print("测试3: 并发分配（同一袋血不能重复分配）")
    print("=" * 60)
    
    # 先获取一家医院
    r = requests.get(f"{BASE_URL}/hospitals/")
    hospitals = r.json()
    hospital_id = hospitals[0]['id']
    
    # 创建申请
    r = requests.post(f"{BASE_URL}/requests/", json={
        "hospital_id": str(hospital_id),
        "patient_blood_type": "A",
        "patient_rh_type": "POSITIVE",
        "component": "RBC",
        "quantity_units": 1,
        "urgency": "ROUTINE",
        "patient_name": "并发测试患者",
        "patient_age": 30,
        "diagnosis": "测试诊断"
    })
    request = r.json()
    
    # 匹配
    r = requests.post(f"{BASE_URL}/requests/match", json={
        "request_id": str(request['id'])
    })
    match_result = r.json()
    
    if match_result['total_matched'] == 0:
        print("❌ 没有匹配到血袋，无法测试")
        return False
    
    print(f"匹配到血袋: {match_result['matched_items'][0]['bag_number']}")
    
    # 第一次确认调拨（应该成功）
    r1 = requests.post(f"{BASE_URL}/dispatches/confirm", params={
        "request_id": str(request['id'])
    }, json=match_result['matched_items'])
    
    print(f"第一次确认调拨: {'✅ 成功' if r1.status_code == 200 else '❌ 失败'} - {r1.status_code}")
    
    if r1.status_code != 200:
        print(f"  错误: {r1.text}")
        return False
    
    # 第二次尝试用相同的血袋确认调拨（应该失败）
    r2 = requests.post(f"{BASE_URL}/dispatches/confirm", params={
        "request_id": str(request['id'])
    }, json=match_result['matched_items'])
    
    print(f"第二次确认调拨(相同血袋): {'❌ 失败（符合预期）' if r2.status_code != 200 else '✅ 成功（这是错误！）'} - {r2.status_code}")
    
    if r2.status_code != 200:
        print("✅ 成功！同一袋血不能被重复分配")
        return True
    else:
        print("❌ 严重问题！同一袋血被重复分配了")
        return False

if __name__ == "__main__":
    results = []
    results.append(("Rh血型匹配", test_rh_matching()))
    results.append(("FIFO排序", test_fifo_sorting()))
    results.append(("并发分配", test_concurrent_allocation()))
    
    print("\n" + "=" * 60)
    print("测试总结:")
    print("=" * 60)
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    print(f"\n整体: {'✅ 所有测试通过！' if all_passed else '❌ 部分测试失败'}")
