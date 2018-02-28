# _*_ coding:utf-8 _*_
__author__ = 'Xbc'

from django.conf.urls import url
from apps.user import views

urlpatterns = [
    # url(r'^register$', views.register, name='register'),
    # url(r'^register_handle$', views.register_handle, name='register_handle'),
    url(r'register$', views.RegisterView.as_view(), name='register'),
    url(r'^active/(?P<token>.*)$', views.ActiveView.as_view(), name='active'),
    url(r'^login$', views.LoginView.as_view(), name='login'),
    url(r'^logout$', views.LogoutView.as_view(), name='loginout'),
]