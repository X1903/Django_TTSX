# _*_ coding:utf-8 _*_
__author__ = 'Xbc'

from django.views.generic import View
from django.contrib.auth.decorators import login_required

class LoginRequestView(View):
    @classmethod
    def as_view(cls, **initkwargs):
        # 调用父类的as_view方法
        view = super(LoginRequestView, cls).as_view(**initkwargs)
        # 调用登录判断装饰器
        return login_required(view)

class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        # 调用父类的as_view方法
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        # 调用登录判断装饰器
        return login_required(view)