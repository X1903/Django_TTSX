# _*_ coding:utf-8 _*_
__author__ = 'Xbc'

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from apps.user import views

urlpatterns = [
    # url(r'^register$', views.register, name='register'),  # 注册页面心事
    # url(r'^register_handle$', views.register_handle, name='register_handle'),  # 注册处理
    url(r'^register$', views.RegisterView.as_view(), name='register'),  # 注册
    url(r'^active/(?P<token>.*)$', views.ActiveView.as_view(), name='active'),  # 激活
    url(r'^login$', views.LoginView.as_view(), name='login'),  # 登录
    url(r'^logout$', views.LogoutView.as_view(), name='loginout'),  # 退出登录

    # 手动调用login_required装饰器，相当于放的是login_required装饰器的返回值
    # url(r'^$', login_required(views.UserInfoView.as_view()), name='user'),  # 用户中心-信息页
    # url(r'^order$', login_required(views.UserOrderView.as_view()), name='order'),  # 用户中心-订单页
    # url(r'^address$', login_required(views.UserAddressView.as_view()), name='address'),  # 用户中心地址页

    url(r'^$', views.UserInfoView.as_view(), name='user'),
    url(r'^order/(?P<page>\d+)$', views.UserOrderView.as_view(), name='order'), # 用户中心-订单页
    url(r'^address$', views.UserAddressView.as_view(), name='address'), # 用户中心-地址页
]