import requests
import random
# 사용자 이름을 포함한 데이터를 생성
data = {"orderItems":[{"id": str(random.randint(1,9)), "name":"name"+str(random.randint(1,9)), "original_price": str(random.randint(1,9)*1000), "price": str(random.randint(1,9)*1000+300)}]}

# POST 요청을 보내고 응답을 받음
response = requests.post("http://localhost:4440/order_request", json=data)

# 응답 데이터를 출력
print(response.json())
