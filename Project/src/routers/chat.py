from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
from openai import OpenAI
from ai_config import OPENAI_API_KEY, OPENAI_BASE_URL, AI_MODEL
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/chat", tags=["AI对话"])

# 全局会话存储：{user_id: [消息历史列表]}
# 简单用内存存，重启就丢，进阶加分项可以改成Redis持久化
sessions = {}

# 初始化AI客户端
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# ========== Tool定义：让AI可以调用的函数 ==========
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_note_by_id",
            "description": "根据笔记ID查询笔记的完整内容，包括标题和正文",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_id": {
                        "type": "integer",
                        "description": "要查询的笔记ID"
                    }
                },
                "required": ["note_id"]
            }
        }
    }
]

def get_note_by_id(note_id: int) -> dict:
    """实际执行：从数据库查笔记"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, created_at FROM notes WHERE id = %s", (note_id,))
    note = cursor.fetchone()
    cursor.close()
    conn.close()
    if not note:
        return {"error": f"笔记{note_id}不存在"}
    return {
        "id": note["id"],
        "title": note["title"],
        "content": note["content"],
        "created_at": str(note["created_at"])
    }

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

@router.post("", summary="和AI对话（支持Tool Use）")
def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """和AI对话，AI可以自动调用查询笔记的工具"""
    user_id = current_user.get("sub", "unknown")
    session_key = f"{user_id}_{req.session_id}"

    # 1. 取出这个用户的会话历史
    if session_key not in sessions:
        sessions[session_key] = [
            {"role": "system", "content": "你是JotangNote的AI助手，可以帮用户管理笔记。用户问你笔记内容时，你可以调用get_note_by_id工具查询。"}
        ]

    history = sessions[session_key]

    # 2. 把用户新消息加入历史
    history.append({"role": "user", "content": req.message})

    # 3. 调用AI，带上工具定义
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=history,
        tools=TOOLS,
        tool_choice="auto"  # 让AI自己决定要不要调用工具
    )

    ai_message = response.choices[0].message

    # 4. 判断AI是不是要调用工具
    if ai_message.tool_calls:
        # 把AI要调用工具的这条消息也存进历史（用户看不见，但要算上下文）
        history.append(ai_message.model_dump(exclude_none=True))

        # 逐个执行工具调用
        for tool_call in ai_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print(f"[AI调用工具] {function_name} 参数: {function_args}")

            # 执行我们本地的函数
            if function_name == "get_note_by_id":
                result = get_note_by_id(function_args["note_id"])
            else:
                result = {"error": "未知工具"}

            # 把工具返回结果存进历史
            history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })

        # 5. 把工具结果再发给AI，让它生成最终回复
        second_response = client.chat.completions.create(
            model=AI_MODEL,
            messages=history
        )
        final_message = second_response.choices[0].message.content
        history.append({"role": "assistant", "content": final_message})

        return {"reply": final_message, "tool_used": True}

    else:
        # 没调用工具，直接返回AI回复
        history.append({"role": "assistant", "content": ai_message.content})
        return {"reply": ai_message.content, "tool_used": False}

@router.get("/history", summary="查看当前会话历史")
def get_history(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("sub", "unknown")
    key = f"{user_id}_default"
    return {"history": sessions.get(key, [])}
