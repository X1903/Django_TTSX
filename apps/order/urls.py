# _*_ coding:utf-8 _*_
__author__ = 'Xbc'

from django.conf.urls import url
from apps.order import views

urlpatterns = [
    url(r'^place$', views.OrderPlaceView.as_view(), name='place'), # 提交订单页面显示
    url(r'^commit$', views.OrderCommitView.as_view(), name='commit'), # 订单创建

]
