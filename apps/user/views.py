import re

from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired

from apps.user.models import User
from celery_tasks.tasks import send_register_active_email

# Create your views here.

def register(request):
    '''显示注册页面以及注册处理'''
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        # 接受参数
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpassword = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 参数校验
        # 校验参数完整性
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验两次密码是否相同
        if cpassword != password:
            return render(request, 'register.html', {'errmsg': '两次密码不相同'})

        # 校验是否同意协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请购选用户使用协议'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱不合法'})

        # 校验用户名是否存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 业务处理: 用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 返回应答:: 跳转到首页
        return redirect(reverse('goods:index'))


def register_handle(request):
    '''注册处理'''

    # 接受参数
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    cpassword = request.POST.get('cpwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')

    # 参数校验
    # 校验参数完整性
    if not all([username, password, email]):
        return render(request, 'register.html', {'errmsg': '数据不完整'})

    # 校验两次密码是否相同
    if cpassword != password:
        return render(request, 'register.html', {'errmsg': '两次密码不相同'})

    # 校验是否同意协议
    if allow != 'on':
        return render(request, 'register.html', {'errmsg': '请购选用户使用协议'})

    # 校验邮箱
    if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '邮箱不合法'})

    # 校验用户名是否存在
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None

    if user:
        return render(request, 'register.html', {'errmsg': '用户名已存在'})

    # 业务处理: 用户注册
    user = User.objects.create_user(username, email, password)
    user.is_active = 0
    user.save()

    # 返回应答:: 跳转到首页
    return redirect(reverse('goods:index'))


class RegisterView(View):
    '''显示注册'''
    def get(self, request):
        '''显示'''
        return render(request, 'register.html')

    def post(self, request):
        '''注册'''
        # 接受参数
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpassword = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 参数校验
        # 校验参数完整性
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验两次密码是否相同
        if cpassword != password:
            return render(request, 'register.html', {'errmsg': '两次密码不相同'})

        # 校验是否同意协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请购选用户使用协议'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱不合法'})

        # 校验用户名是否存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 业务处理: 用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 加密用户的身份信息, 生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm':user.id}
        # 加密数据
        token = serializer.dumps(info)  # bytes类型
        token = token.decode() # 转换成str

        # 使用celery给用户的注册邮箱发送激活邮件, 激活邮件中需要包含激活链接: /user/active/用户id
        # /user/active/token
        send_register_active_email.delay(email, username, token)

        # 返回应答:: 跳转到首页
        return redirect(reverse('goods:index'))

# user/active/激活token信息
class ActiveView(View):
    def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 3600)

        try:
            # 解密数据
            info = serializer.loads(token)  # 内部自动转换成bytes类型

            # 获取待激活的用户id
            user_id = info['confirm']

            # 业务处理: 激活账号
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 返回应答, 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired:
            # 激活链接以失效
            # 实际开发:
            return HttpResponse('激活链接已失效')

# django框架会给request对象增加一个属性user
# 如果用户已经登录, user是认证系统用户模型类的一个实例对象
# 如果用户没有登录, user是AnonymousUser类的实例对象
# 在模板文件中可以直接使用request的user属性

class LoginView(View):
    '''登录'''
    def get(self, request):
        '''显示登录页面'''
        # 先尝试从cookie中获取username
        if 'username' in request.COOKIES:
            # 记住用户名
            username = request.COOKIES['username']
            checked = 'checked'
        else:
            # 没有用户名
            username = ''
            checked = ''
        return render(request, 'login.html', {'username':username, 'checked':checked})

    def post(self, request):
        '''登录校验'''

        # 接收参数
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')

        #参数校验
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        # 业务处理: 登录校验
        # 根据用户名和密码查找用户信息
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户激活状态
                # 记录用户的登录状态
                login(request, user)

                # 跳转到用户首页
                response = redirect(reverse('goods:index'))

                # 判断是否需要记住用户名
                if remember == 'on':
                    # 需要记住用户名
                    # 设置一个cookie信息,保存用户登录信息
                    # 设置cookie需要调用set_cookie方式, set_cookie他是HttpResponse对象的方法
                    # HttpResponseRedirect是HttpResponse的子类
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    # 不需要记住用户名
                    response.delete_cookie('username')

                # 跳转到用户首页
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '账号未激活'})

        else:
            # 用户名密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})

        # 返回应答

class LogoutView(View):
    '''退出登录'''
    def get(self, request):
        '''退出登录'''
        # 清楚用户的登录信息
        logout(request)
        # 返回应答跳转到登录页面
        return render(request, 'login.html')
