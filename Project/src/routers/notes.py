from fastapi import APIRouter, Depends, HTTPException
import json
import pika
import pymysql
from database import get_db
from schemas import NoteCreate, NoteUpdate
from auth import get_current_user
from redis_client import redis_client, get_cache_key, CACHE_EXPIRE
from mq import get_rabbitmq_channel, NOTE_QUEUE

router = APIRouter(prefix="/notes", tags=["笔记"])

def get_user_id_by_username(username: str) -> int:
    """根据用户名查用户ID"""
    conn = next(get_db())
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user["id"]

# ========== 查询笔记（带Redis缓存） ==========
@router.get("/{note_id}", summary="查询单篇笔记")
def get_note(note_id: int, current_user: dict = Depends(get_current_user)):
    """查询笔记：先查Redis缓存，没有再查MySQL，然后回写缓存"""
    cache_key = get_cache_key(note_id)

    # 1. 先查Redis
    cached = redis_client.get(cache_key)
    if cached is not None:
        # 缓存穿透处理：如果缓存的是None，说明这篇笔记不存在
        if cached == "__NOT_EXIST__":
            raise HTTPException(status_code=404, detail="笔记不存在")
        return json.loads(cached)

    # 2. 缓存没命中，查MySQL
    conn = next(get_db())
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE id = %s", (note_id,))
    note = cursor.fetchone()
    cursor.close()
    conn.close()

    if not note:
        # 缓存穿透处理：把不存在的结果也缓存起来，设短过期时间
        redis_client.setex(cache_key, 60, "__NOT_EXIST__")
        raise HTTPException(status_code=404, detail="笔记不存在")

    # 3. 把MySQL结果写入Redis缓存
    note_dict = dict(note)
    note_dict["created_at"] = note_dict["created_at"].isoformat()
    note_dict["updated_at"] = note_dict["updated_at"].isoformat()
    redis_client.setex(cache_key, CACHE_EXPIRE, json.dumps(note_dict))

    return note_dict

# ========== 新增笔记（异步，通过MQ） ==========
@router.post("", summary="新增笔记")
def create_note(note: NoteCreate, current_user: dict = Depends(get_current_user)):
    """新增笔记：投递消息到MQ，立即返回，后台消费者执行"""
    user_id = get_user_id_by_username(current_user["username"])

    # 构造消息
    message = {
        "action": "create",
        "data": {
            "user_id": user_id,
            "title": note.title,
            "content": note.content
        }
    }

    # 投递到RabbitMQ
    connection, channel = get_rabbitmq_channel()
    channel.basic_publish(
        exchange="",
        routing_key=NOTE_QUEUE,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2)  # 消息持久化
    )
    connection.close()

    return {"msg": "笔记创建任务已提交，请稍后查询", "user_id": user_id}

# ========== 修改笔记（异步，通过MQ） ==========
@router.put("/{note_id}", summary="修改笔记")
def update_note(note_id: int, note: NoteUpdate, current_user: dict = Depends(get_current_user)):
    """修改笔记：投递消息到MQ，立即返回"""
    user_id = get_user_id_by_username(current_user["username"])

    # 先校验笔记归属（同步查一下，防止改别人的）
    conn = next(get_db())
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM notes WHERE id = %s", (note_id,))
    db_note = cursor.fetchone()
    cursor.close()
    conn.close()

    if not db_note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    if db_note["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="无权修改别人的笔记")

    message = {
        "action": "update",
        "data": {
            "note_id": note_id,
            "user_id": user_id,
            "title": note.title,
            "content": note.content
        }
    }

    connection, channel = get_rabbitmq_channel()
    channel.basic_publish(
        exchange="",
        routing_key=NOTE_QUEUE,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

    # 缓存一致性：修改后删除旧缓存
    redis_client.delete(get_cache_key(note_id))

    return {"msg": "笔记修改任务已提交"}

# ========== 删除笔记（异步，通过MQ） ==========
@router.delete("/{note_id}", summary="删除笔记")
def delete_note(note_id: int, current_user: dict = Depends(get_current_user)):
    """删除笔记：投递消息到MQ，立即返回"""
    user_id = get_user_id_by_username(current_user["username"])

    # 校验归属
    conn = next(get_db())
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM notes WHERE id = %s", (note_id,))
    db_note = cursor.fetchone()
    cursor.close()
    conn.close()

    if not db_note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    if db_note["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="无权删除别人的笔记")

    message = {
        "action": "delete",
        "data": {
            "note_id": note_id,
            "user_id": user_id
        }
    }

    connection, channel = get_rabbitmq_channel()
    channel.basic_publish(
        exchange="",
        routing_key=NOTE_QUEUE,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

    # 缓存一致性：删除后清除缓存
    redis_client.delete(get_cache_key(note_id))

    return {"msg": "笔记删除任务已提交"}
