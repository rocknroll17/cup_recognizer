import requests

# 사용자 이름을 포함한 데이터를 생성
data = {"username": "user123"}

# POST 요청을 보내고 응답을 받음
response = requests.post("http://localhost:4440/", json=data)

# 응답 데이터를 출력
print(response.json())