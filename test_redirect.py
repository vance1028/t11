import requests

# 测试不带末尾斜杠的请求
print("=== 测试 /inventory（不带末尾斜杠）===")
resp = requests.get(
    "http://localhost:8472/api/v1/inventory",
    params={"only_in_stock": "true"},
    allow_redirects=False
)
print(f"状态码: {resp.status_code}")
print(f"响应头: {dict(resp.headers)}")
if resp.status_code in [301, 302, 307, 308]:
    print(f"重定向到: {resp.headers.get('Location')}")

print("\n=== 测试 /inventory/（带末尾斜杠）===")
resp2 = requests.get(
    "http://localhost:8472/api/v1/inventory/",
    params={"only_in_stock": "true"},
    allow_redirects=False
)
print(f"状态码: {resp2.status_code}")
