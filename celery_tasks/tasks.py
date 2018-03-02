# _*_ coding:utf-8 _*_
__author__ = 'Xbc'

from django.conf import settings
from django.core.mail import send_mail
from django.template import loader

# 导入Celery类的对象
from celery import Celery

# 这两行代码需要在启动worker的一段打开
# 初始化Django所依赖的环境
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GitHub_TTSX.settings")
django.setup()
# 启动命令 celery -A celery_tasks.tasks worker -l info

# celery worker启动的一端导入模型类必须在django.setup()之后
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner


# 创建一个Celery的对象
app = Celery('celery_tasks.tsks', broker='redis://192.168.120.129:6379/5')


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



@app.task
def generate_static_index_html():
    """生成一个静态首页文件"""
    # 获取商品分类信息
    types = GoodsType.objects.all()

    # 获取首页轮播商品的信息
    index_banner = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销活动的信息
    promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:
        # 根据type查询type种类首页展示的文字商品信息和图片商品信息
        title_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
        image_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        # 给type对象增加两个属性title_banner, image_banner
        # 分别保存type种类首页展示的文字商品信息和图片商品信息
        type.title_banner = title_banner
        type.image_banner = image_banner

    # 获取登录用户购物车商品的数目
    cart_count = 0

    # 组织模板上下文
    context = {'types': types,
               'index_banner': index_banner,
               'promotion_banner': promotion_banner,
               'cart_count': cart_count}

    # 渲染产生静态首页html内容
    # 1.加载模板, 获取模板对象
    temp = loader.get_template('static_index.html')
    # 2.模板渲染，产生替换后的html内容
    static_html = temp.render(context)

    # 创建一个静态首页文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_html)
