# _*_ coding:utf-8 _*_
__author__ = 'Xbc'

from django.conf.urls import url
from apps.goods import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'), # 首页
    url(r'^index$', views.IndexView.as_view(), name='index'), # 首页

    url(r'^goods/(?P<sku_id>\d+)$', views.DetailView.as_view(), name='detail'),  # 详情页
url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)$', views.ListView.as_view(), name='list'), # 列表页
]