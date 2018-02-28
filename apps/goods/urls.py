# _*_ coding:utf-8 _*_
__author__ = 'Xbc'

from django.conf.urls import url
from apps.goods import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

]