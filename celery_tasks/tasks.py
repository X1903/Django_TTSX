# _*_ coding:utf-8 _*_
__author__ = 'Xbc'

from django.conf import settings
from django.core.mail import send_mail

# 导入Celery类的对象
from celery import Celery

# 这两行代码需要在启动worker的一段打开
# 初始化Django所依赖的环境
# import os
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GitHub_TTSX.settings")
# 启动命令 celery -A celery_tasks.tasks worker -l info


# 创建一个Celery的对象
app = Celery('celery_tasks.tsks', broker='redis://192.168.120.255:6379/5')


# 定义任务
@app.task
def send_register_active_email(to_email, username, token):
    '''发送激活邮件'''

    # 组织邮件内容
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>%s, 欢迎你成为天天生鲜注册会员</h1>请点击以下链接激活您的账户<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
    username, token, token)

    # 给用户的注册邮箱发送激活邮件, 激活邮件中需要包含激活链接: /user/active/用户id
    # /user/active/token
    send_mail(subject, message, sender, receiver, html_message=html_message)