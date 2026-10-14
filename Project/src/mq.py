import pika

# RabbitMQ连接配置
RABBITMQ_CONFIG = {
    "host": "127.0.0.1",
    "port": 5672,
    "virtual_host": "/",
    "credentials": pika.PlainCredentials("guest", "guest")
}

NOTE_QUEUE = "note_operations"

def get_rabbitmq_channel():
    """获取RabbitMQ连接和通道"""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(**RABBITMQ_CONFIG)
    )
    channel = connection.channel()
    channel.queue_declare(queue=NOTE_QUEUE, durable=True)
    return connection, channel
