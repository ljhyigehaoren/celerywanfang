# celery 的配置文件比较多，所以这里我们可以编辑一个配置文件
# 官方配置文档：
# http://docs.celeryproject.org/en/latest/userguide/configuration.html
# 查询每个配置项的含义。
from __future__ import absolute_import
from datetime import timedelta
#这一次创建 app，并没有直接指定 broker(消息中间件来接收和发送任务消息) 和 backend(存储结果)。而是在配置文件中。
CELERY_RESULT_BACKEND = 'redis://118.24.255.219:6380/5'
BROKER_URL = 'redis://118.24.255.219:6380/6'
CELERY_TIMEZONE='Asia/Shanghai'
CELERY_ENABLE_UTC=True
CELERY_ACCEPT_CONTENT=['json']
CELERY_TASK_SERIALIZER='json'
CELERY_RESULT_SERIALIZER='json'
CELERY_IMPORTS = [
    'tasks',
]

# CELERYBEAT_SCHEDULE = {
#     'tasks':{
#         'task':'tasks.crawl_pageurl_and_detailurl',
#         'schedule':timedelta(seconds=5),
#         'args':(参数),
#     }
# }


