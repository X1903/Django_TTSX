from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.views.generic import View
from django.core.cache import cache

from django_redis import get_redis_connection
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU
from apps.order.models import OrderGoods


from celery_tasks.tasks import generate_static_index_html
# Create your views here.

# http://127.0.01:8000
class IndexView(View):
    '''首页'''
    def get(self, request):
        '''显示'''

        # 尝试先从换从中获取数据
        context = cache.get('index_page_data')
        if context is None:
            print('*'*20, '首页缓存')
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


            # 组织缓存的数据
            context = {'types': types,
                       'index_banner': index_banner,
                       'promotion_banner': promotion_banner,
                       'cart_count': cart_count}

            # 设置缓存  poickle
            cache.set('index_page_data', context, 3600)


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
        context.update(cart_count=cart_count)

        # 渲染产生静态文件

        # 使用模板
        return render(request, 'index.html', context)

# 访问商品的详情页面时候，需要传递商品的id
# 前端向后端传递参数的方式:
    # 1. get（只涉及到数据的获取) /goods?sku_id=商品id
    # 2. post(涉及到数据的修改) 传递
    # 3. url捕获参数 /goods/商品id
# flask: restful api的设计
# /goods/商品id
# /goods/10000
class DetailView(View):
    '''详情页面'''
    def get(self, request, sku_id):
        '''显示详情页'''
        # 获取商品信息
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在,, 跳转到首页
            return render(reversed('goods:index'))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取和商品同一分类的2个新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取商品的评论信息
        order_skus = OrderGoods.objects.filter(sku=sku).exclude(comment='').order_by('-uodate_time')

        # 获取和sku商品同一SPU的其他规格的商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=sku_id)

        # # 获取用户登录购物车的商品条目数
        cart_count = 0

        # 获取用户
        user = request.user
        if user.is_authenticated():
            # 用户已经登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

            # 添加用户浏览记录
            history_key = 'history_%d' % user.id
            # 先删除从redis雷彪中删除元素的sku_id
            conn.lrem(history_key, 0, sku_id)
            # 把sku_id 加入到redis对应列表的左侧
            conn.lpush(history_key, sku_id)
            # 保留用户最近浏览的五个商品的ID
            conn.ltrim(history_key, 0, 4)


        # 组织模板上下文
        context = {'types': types,
                   'sku': sku,
                   'new_skus': new_skus,
                   'same_spu_skus': same_spu_skus,
                   'order_skus': order_skus,
                   'cart_count': cart_count
                   }

        # 使用模板
        return render(request, 'detail.html', context)

# 访问列表页面的时候，需要传递的参数
# 种类id(type_id) 页码(page) 排序方式(sort)
# /list?type_id=种类id&page=页码&sort=排序方式
# /list/种类id/页码/排序方式
# /list/种类id/页码?sort=排序方式
# /list/7/1/?sort

class ListView(View):
    """列表页面"""
    def get(self, request, type_id, page):
        '''显示渲染页面'''

        # 获取type_id对应的分类信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 商品种类不存在，跳转到首页
            return redirect(reverse('goods:index'))

        # 获取商品分类信息
        types = GoodsType.objects.all()

        # 获取排序方式 获取分类商品的信息
        sort = request.GET.get('sort', 'default')
        # sort=='default':按照默认方式(商品id)排序
        # sort=='price':按照商品的价格(price)排序
        # sort=='hot':按照商品的销量(sales)排序

        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            # 默认排序
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')


        # 分页
        paginator = Paginator(skus, 1)

        # 处理页码
        page = int(page)
        if page > paginator.num_pages or page <= 0:
            # 默认显示第1页
            page = 1

        # 获取第page页的Page对象
        skus_page = paginator.page(page)

        # 页码处理(页面最多只显示出5个页码)
        # 1.总页数不足5页，显示所有页码
        # 2.当前页是前3页，显示1-5页
        # 3.当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 获取分类的2个新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取用户购车中的商品的条目数
        cart_count = 0
        # 获取user
        user = request.user
        if user.is_authenticated():
            # 用户已登录
            # 获取登录用户购物车中商品的条目数
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context = {'types': types,
                   'type': type,
                   'skus_page': skus_page,
                   'pages':pages,
                   'new_skus': new_skus,
                   'cart_count': cart_count,
                   'sort':sort}

        # 使用模板
        return render(request, 'list.html', context)



