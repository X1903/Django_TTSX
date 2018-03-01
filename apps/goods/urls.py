# _*_ coding:utf-8 _*_
__author__ = 'Xbc'

from django.conf.urls import url
from apps.goods import views

urlpatterns = [
    url(r'^index$', views.IndexView.as_view(), name='index'), # 首页
]