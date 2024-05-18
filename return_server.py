from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import uvicorn
import qr_reader as qr

app = FastAPI()

templates = Jinja2Templates(directory="return_templates")

@app.get("/return")
def return_bottle(request: Request):
    return templates.TemplateResponse("return.html", {"request": request})

@app.post("/qr_reader")
def qr_reader():
    qr.instance()

if __name__ == "__main__":
    uvicorn.run("return_server:app", host="0.0.0.0", port=4440, reload=True)