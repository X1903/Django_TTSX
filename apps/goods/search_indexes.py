# _*_ coding:utf-8 _*_
__author__ = 'Xbc'

from haystack import indexes
# 导入你的模型类
from apps.goods.models import GoodsSKU


# 指定对于某个类的某些数据建立索引
# 索引类名称一般格式: 模型类名+Index
class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    # 索引字段: use_template=True说明根据哪些字段的内容建立索引数据, 这些字段会放在文件中来指定
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        # 返回你的模型类
        return GoodsSKU

    # 这个方法返回的是哪些数据，就会对哪些数据建立索引
    def index_queryset(self, using=None):
        return self.get_model().objects.all()
