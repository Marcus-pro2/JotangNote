from fastapi import APIRouter, Depends, HTTPException
import pymysql
from database import get_db
from schemas import UserRegister, UserLogin
from auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/users", tags=["用户"])

@router.post("/register", summary="用户注册")
def register(user: UserRegister):
    """用户注册：新增一条用户记录"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")

        # 插入新用户
        password_hash = hash_password(user.password)
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (user.username, password_hash)
        )
        conn.commit()
        return {"msg": "注册成功", "username": user.username}
    finally:
        cursor.close()
        conn.close()

@router.post("/login", summary="用户登录")
def login(user: UserLogin):
    """用户登录：校验账号密码，返回JWT token"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (user.username,))
        db_user = cursor.fetchone()
        if not db_user or not verify_password(user.password, db_user["password_hash"]):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        token = create_access_token(user.username)
        return {"access_token": token, "token_type": "bearer", "user_id": db_user["id"]}
    finally:
        cursor.close()
        conn.close()
