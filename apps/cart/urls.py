# _*_ coding:utf-8 _*_
__author__ = 'Xbc'

from django.conf.urls import url
from apps.cart import views

urlpatterns = [


    # url(r'^ajax_request$', AjaxTestView.as_view()),
    # # url(r'^ajax_handle$', AjaxHandleView.as_view()),
    #
    url(r'^$', views.CartInfoView.as_view(), name='show'), # 购物车页面显示
    url(r'^add$', views.CartAddView.as_view(), name='add'), # 购物车记录添加

]