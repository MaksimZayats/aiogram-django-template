from os import getenv

broker_url = getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

task_always_eager = getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"
task_eager_propagates = getenv("CELERY_TASK_EAGER_PROPAGATES", "false").lower() == "true"
task_ignore_result = getenv("CELERY_TASK_IGNORE_RESULT", "false").lower() == "true"

timezone = "UTC"
enable_utc = True
