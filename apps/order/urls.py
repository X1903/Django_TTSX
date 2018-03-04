# _*_ coding:utf-8 _*_
__author__ = 'Xbc'

from django.conf.urls import url
from apps.order import views

urlpatterns = [
    url(r'^place$', views.OrderPlaceView.as_view(), name='place'), # 提交订单页面显示
    url(r'^commit$', views.OrderCommitView.as_view(), name='commit'), # 订单创建
    url(r'^pay$', views.OrderPayView.as_view(), name='pay'), # 订单支付
    url(r'^check$', views.CheckPayView.as_view(), name='check'), # 支付结果查询
    url(r'^comment/(?P<order_id>.*)$', views.OrderCommentView.as_view(), name='comment'), # 订单评论

]
