# _*_ coding:utf-8 _*_
__author__ = 'XbcdX'

from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings
import os

# 保存文件的时候, Django系统会调用Storage类中的save方法, save方法内部会调用文件存储类中的_save方法
# _save方法的返回值,会保存在表的image字段中
# 自定义文件存储类
# 在调用save方法前, django系统会先调用exists方法, 判断文件的系统是否存在

class FDFSStorage(Storage):
    '''fastdfs系统文件存储类'''

    def __init__(self, client_conf=None, nginx_url=None):
        """初始化"""
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if nginx_url is None:
            nginx_url = settings.FDFS_NGINX_URL
        self.nginx_url = nginx_url



    def _open(self, name, mode='rb'):
        '''打开文件时使用'''
        pass

    def _save(self, name, content):
        '''保存文件时使用'''
        # name: 上传文件
        # content: 包含上传文件内容的File对象

        # 把文件上传到fastdfs系统中
        # client = Fdfs_client('/Users/hui/PycharmProjects/GitHub_TTSX/utils/fdfs/client.conf')
        client = Fdfs_client(self.client_conf)

        # 获取上传文件内容
        content = content.read()
        # 把文件上传到fastdfs中
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,    # 上传文件的ID
        #     'Status': 'Upload successed.',       # 上传是否成功
        #     'Local file name': local_file_name,
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }
        res = client.upload_by_buffer(content)

        # 判断上传文件是否成功
        if res.get('Status') != 'Upload successed.':
            # 上传文件到fdfs失败
            raise Exception('上传文件到fdfs系统失败')

        # 获取文件的ID
        file_id = res.get('Remote file_id')

        # 返回文件ID
        return file_id

    def exists(self, name):
        '''判断文件是否存在'''
        return False

    def url(self, name):
        '''返回一个可访问到的url路径'''

        # name : 文件的id
        return self.nginx_url + name




