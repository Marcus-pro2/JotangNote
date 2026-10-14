import redis

# Redis连接配置
REDIS_CONFIG = {
    "host": "127.0.0.1",
    "port": 6379,
    "db": 0,
    "decode_responses": True  # 自动把bytes转成str
}

redis_client = redis.Redis(**REDIS_CONFIG)

# 缓存过期时间（秒）
CACHE_EXPIRE = 300  # 5分钟

def get_cache_key(note_id: int) -> str:
    """生成笔记缓存的key"""
    return f"note:{note_id}"
