from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# FastAPI 앱 생성
app = FastAPI()

# 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="templates")

# 현재 버튼 목록
buttons = []

# 현재 버튼 목록을 반환하는 핸들러 함수 정의
@app.get("/", response_class=HTMLResponse)
async def read_buttons(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "buttons": buttons})

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
