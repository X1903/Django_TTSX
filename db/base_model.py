# _*_ coding:utf-8 _*_
__author__ = 'Xbc'



from django.db import models

class BaseModel(models.Model):
    '''抽象模型基类'''

    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    uodate_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')
    is_delete = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        '''指定这个类是抽象模型类'''

        abstract = True