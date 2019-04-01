from __future__ import absolute_import,unicode_literals
from celery import Celery


#方式一：
# app = Celery(
#     'tasks',
#     # broker='',
#     # backend='',
# )

#方式二：
app = Celery(
    'celerywanwang',
)

app.config_from_object('celeryconfig')

if __name__ == '__main__':

    app.start()