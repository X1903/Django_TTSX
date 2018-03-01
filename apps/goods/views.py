from django.shortcuts import render
from django.views.generic import View
from django_redis import get_redis_connection
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner


# Create your views here.

# http://127.0.01:8000
class IndexView(View):
    '''首页'''
    def get(self, request):
        '''显示'''

        # 获取商品分类信息
        types = GoodsType.objects.all()

        # 获取首页轮播商品的信息
        index_banner = IndexGoodsBanner.objects.all().order_by('index')

        # 获取首页促销商品的的信息
        promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

        # types_goods_banner = IndexTypeGoodsBanner.objects.all()
        for type in types:
            # 根据type查询type种类首页展示的文字商品信息和图片商品信息
            title_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
            image_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
            # 给type对象增加两个属性title_banner, image_banner
            # 分别保存type种类首页展示的文字商品信息和图片商品信息
            type.title_banner = title_banner
            type.image_banner = image_banner


        # 获取登录用户购物车商品数目
        cart_count = 0
        # 获取用户
        user = request.user
        if user.is_authenticated():
            # 用户已经登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)


        # 组织模板上下文
        content = {'types': types,
                   'index_banner':index_banner,
                   'promotion_banner':promotion_banner,
                   'cart_count':cart_count}

        # 使用模板
        return render(request, 'index.html', content)