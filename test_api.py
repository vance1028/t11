import requests

BASE_URL = "http://localhost:8472/api/v1"

print("=== 测试登录接口 ===")
login_resp = requests.post(
    f"{BASE_URL}/auth/login/json",
    json={"username": "admin", "password": "admin123"}
)
print(f"登录状态: {login_resp.status_code}")
print(f"登录响应: {login_resp.text[:200]}")

if login_resp.status_code == 200:
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== 测试医院列表 ===")
    hosp_resp = requests.get(f"{BASE_URL}/hospitals", headers=headers)
    print(f"医院列表状态: {hosp_resp.status_code}")
    if hosp_resp.status_code == 200:
        hospitals = hosp_resp.json()
        print(f"医院数量: {len(hospitals)}")
        for h in hospitals[:3]:
            print(f"  - {h['name']}")
    else:
        print(f"错误: {hosp_resp.text}")
    
    print("\n=== 测试库存列表 ===")
    inv_resp = requests.get(f"{BASE_URL}/inventory", headers=headers)
    print(f"库存列表状态: {inv_resp.status_code}")
    if inv_resp.status_code == 200:
        bags = inv_resp.json()
        print(f"血袋数量: {len(bags)}")
        if bags:
            print(f"第一袋: {bags[0]['bag_number']} - {bags[0]['blood_type']}{bags[0]['rh_type']} {bags[0]['component']}")
    else:
        print(f"错误: {inv_resp.text}")
    
    print("\n=== 测试申请列表 ===")
    req_resp = requests.get(f"{BASE_URL}/requests", headers=headers)
    print(f"申请列表状态: {req_resp.status_code}")
    if req_resp.status_code == 200:
        reqs = req_resp.json()
        print(f"申请数量: {len(reqs)}")
        for r in reqs:
            print(f"  - {r['request_number']} {r['patient_blood_type']}{r['patient_rh_type']} {r['component']} x{r['quantity_units']}")
    else:
        print(f"错误: {req_resp.text}")
    
    print("\n=== 测试调拨列表 ===")
    dis_resp = requests.get(f"{BASE_URL}/dispatches", headers=headers)
    print(f"调拨列表状态: {dis_resp.status_code}")
    if dis_resp.status_code == 200:
        disps = dis_resp.json()
        print(f"调拨数量: {len(disps)}")
    else:
        print(f"错误: {dis_resp.text}")
    
    print("\n=== 测试看板统计 ===")
    dash_resp = requests.get(f"{BASE_URL}/dashboard/stats", headers=headers)
    print(f"看板状态: {dash_resp.status_code}")
    if dash_resp.status_code == 200:
        stats = dash_resp.json()
        print(f"总库存: {stats['total_inventory']}")
        print(f"待处理申请: {stats['total_requests_pending']}")
    else:
        print(f"错误: {dash_resp.text}")
else:
    print("登录失败，无法继续测试")
