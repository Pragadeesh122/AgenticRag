import os
from arq.connections import RedisSettings
from dotenv import load_dotenv

# Import Tasks
from tasks.document_tasks import process_document_task

# Ensure environment is loaded
load_dotenv()

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", "6379"))

# Setup ARQ Redis Settings
WorkerSettings = type(
    "WorkerSettings",
    (),
    {
        "redis_settings": RedisSettings(host=redis_host, port=redis_port),
        "functions": [process_document_task],
        "on_startup": None,
        "on_shutdown": None,
    }
)
