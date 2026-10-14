import json
import pymysql
from database import get_db
from mq import get_rabbitmq_channel, NOTE_QUEUE

def execute_create(data: dict):
    """执行新增笔记"""
    conn = next(get_db())
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO notes (user_id, title, content) VALUES (%s, %s, %s)",
            (data["user_id"], data["title"], data["content"])
        )
        conn.commit()
        print(f"[消费者] 新增笔记成功: {data['title']}")
    finally:
        cursor.close()
        conn.close()

def execute_update(data: dict):
    """执行修改笔记"""
    conn = next(get_db())
    cursor = conn.cursor()
    try:
        # 幂等性处理：先查笔记是否存在
        cursor.execute("SELECT id FROM notes WHERE id = %s", (data["note_id"],))
        if not cursor.fetchone():
            print(f"[消费者] 笔记{data['note_id']}不存在，跳过修改")
            return

        # 动态拼接更新字段
        update_fields = []
        params = []
        if data.get("title") is not None:
            update_fields.append("title = %s")
            params.append(data["title"])
        if data.get("content") is not None:
            update_fields.append("content = %s")
            params.append(data["content"])

        if not update_fields:
            print("[消费者] 没有需要更新的字段")
            return

        params.append(data["note_id"])
        sql = f"UPDATE notes SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(sql, params)
        conn.commit()
        print(f"[消费者] 修改笔记成功: id={data['note_id']}")
    finally:
        cursor.close()
        conn.close()

def execute_delete(data: dict):
    """执行删除笔记"""
    conn = next(get_db())
    cursor = conn.cursor()
    try:
        # 幂等性处理：先查是否存在
        cursor.execute("SELECT id FROM notes WHERE id = %s", (data["note_id"],))
        if not cursor.fetchone():
            print(f"[消费者] 笔记{data['note_id']}不存在，跳过删除")
            return

        cursor.execute("DELETE FROM notes WHERE id = %s", (data["note_id"],))
        conn.commit()
        print(f"[消费者] 删除笔记成功: id={data['note_id']}")
    finally:
        cursor.close()
        conn.close()

def callback(ch, method, properties, body):
    """MQ消息回调"""
    try:
        message = json.loads(body)
        action = message.get("action")
        data = message.get("data", {})

        if action == "create":
            execute_create(data)
        elif action == "update":
            execute_update(data)
        elif action == "delete":
            execute_delete(data)
        else:
            print(f"[消费者] 未知操作: {action}")

        # 手动确认消息已处理
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[消费者] 处理消息失败: {e}")
        # 失败时不确认，消息会重新入队
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_worker():
    """启动MQ消费者，一直监听队列"""
    connection, channel = get_rabbitmq_channel()
    channel.basic_qos(prefetch_count=1)  # 每次只取一条消息
    channel.basic_consume(queue=NOTE_QUEUE, on_message_callback=callback)
    print("[消费者] 等待消息中...按Ctrl+C退出")
    channel.start_consuming()

if __name__ == "__main__":
    start_worker()
