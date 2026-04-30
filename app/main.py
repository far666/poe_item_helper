from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from rag import query_knowledge

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class ItemRequest(BaseModel):
    item: str

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.post("/analyze")
def analyze_item(request: ItemRequest):
    result = query_knowledge(request.item)
    return {"result": result}