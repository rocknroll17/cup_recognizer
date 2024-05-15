from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import cafe_qr

# FastAPI 앱 생성
app = FastAPI()

# 현재 버튼 목록
buttons = []
templates = Jinja2Templates(directory="templates")
# 현재 버튼 목록을 반환하는 핸들러 함수 정의
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/button")
async def read_button(request: Request):
    global buttons
    return buttons

@app.post("/qr_code")
async def qr_recognizer(request: Request):
    data = await request.json()
    username = data.get("username")
    result = cafe_qr.qr_reading(username)
    if result:
        global buttons
        buttons.remove(username)


# 외부에서의 POST 요청을 받아 새로운 버튼을 추가하는 핸들러 함수 정의
@app.post("/")
async def create_button(request: Request):
    global buttons
    data = await request.json()
    username = data.get("username")
    buttons.append({"username": username})
    return JSONResponse(content={"message": "Button created successfully"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("cafe_server:app", host="0.0.0.0", port=4440, reload=True)