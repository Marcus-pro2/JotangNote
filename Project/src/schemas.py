from pydantic import BaseModel
from datetime import datetime

# 用户注册请求
class UserRegister(BaseModel):
    username: str
    password: str

# 用户登录请求
class UserLogin(BaseModel):
    username: str
    password: str

# 新增笔记请求
class NoteCreate(BaseModel):
    title: str
    content: str

# 修改笔记请求
class NoteUpdate(BaseModel):
    title: str = None
    content: str = None

# 笔记返回
class NoteOut(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
