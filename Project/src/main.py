from fastapi import FastAPI
from routers import users, notes
from database import init_db
import uvicorn

app = FastAPI(title="JotangNote 笔记平台", description="焦糖工作室后端招新入门篇")

# 注册路由
app.include_router(users.router)
app.include_router(notes.router)

@app.on_event("startup")
def startup():
    """启动时初始化数据库"""
    init_db()

@app.get("/", summary="首页")
def index():
    return {"msg": "JotangNote 笔记平台API服务已启动"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
