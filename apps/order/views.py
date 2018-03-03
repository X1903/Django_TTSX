from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.views.generic import View

from apps.user.models import Address
from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods

from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from datetime import datetime


# Create your views here.


# request.GET request.POST ->QueryDict
# 允许一个名字对应多个值
# getlist()
# /order/place
class OrderPlaceView(LoginRequiredMixin, View):
    """提交订单页面显示"""

    def post(self, request):
        """显示"""
        # 获取用户所要购买的商品的id
        sku_ids = request.POST.getlist('sku_ids')

        # 数据校验
        if not all(sku_ids):
            # 跳转到购物车页面
            return redirect(reverse('cart:show'))

        # 业务处理：页面信息获取
        # 获取用户的收货地址信息
        user = request.user
        addrs = Address.objects.filter(user=user)

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        skus = []
        total_count = 0
        total_price = 0
        # 获取用户购买的商品的信息
        for sku_id in sku_ids:
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户所要购买的商品的数量
            count = conn.hget(cart_key, sku_id)
            # 计算商品的小计
            amount = sku.price * int(count)
            # 给sku对象增加属性count和amount, 分别保存用户所要购买的商品的数目和小计
            sku.count = count
            sku.amount = amount
            # 添加商品
            skus.append(sku)

            # 累加计算用户要购买的商品的总数目和总金额
            total_count += int(count)
            total_price += amount

        # 运费：运费的子系统
        transit_price = 10

        # 实付款
        total_pay = total_price + transit_price

        # 组织上下文
        sku_ids = ','.join(sku_ids)  # 1,2,5
        context = {'total_count': total_count,
                   'total_price': total_price,
                   'transit_price': transit_price,
                   'total_pay': total_pay,
                   'addrs': addrs,
                   'skus': skus,
                   'sku_ids': sku_ids}

        # 使用模板
        return render(request, 'place_order.html', context)

        # 订单创建的流程:
        # 接收参数
        # 参数校验
        # 组织订单信息
        # todo: 向df_order_info表中添加一条记录

        # todo: 遍历向df_order_goods中添加记录
        # 获取商品的信息

        # 从redis中获取用户要购买商品的数量

        # todo: 向df_order_goods中添加一条记录

        # todo: 减少商品的库存，增加销量

        # todo: 累加计算用户要购买的商品的总数目和总价格

        # todo: 更新order对应记录中的total_count和total_price

        # todo: 删除购物车中对应的记录

        # 返回应答


# /order/commit
# 前端采用ajax post请求
# 传递的参数：收货地址id(addr_id) 支付方式(pay_method) 用户要购买商品id(sku_ids) 1,2,3
class OrderCommitView(View):
    """订单创建"""

    def post(self, request):
        """订单创建"""
        # 用户登录判断
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # 参数校验
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验地址信息
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            # 地址不存在
            return JsonResponse({'res': 2, 'errmsg': '地址信息错误'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            # 支付方式非法
            return JsonResponse({'res': 3, 'errmsg': '非法的支付方式'})

        # 组织订单信息
        # 订单id: 20171226120020+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transit_price = 10

        # 总数目和总价格
        total_count = 0
        total_price = 0

        # todo: 向df_order_info表中添加一条记录
        order = OrderInfo.objects.create(order_id=order_id,
                                         user=user,
                                         addr=addr,
                                         pay_method=pay_method,
                                         total_count=total_count,
                                         total_price=total_price,
                                         transit_price=transit_price)

        # todo: 遍历向df_order_goods中添加记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        sku_ids = sku_ids.split(',')
        for sku_id in sku_ids:
            # 获取商品的信息
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

            # 获取用户要购买商品的数量
            count = conn.hget(cart_key, sku_id)

            # todo: 向df_order_goods中添加一条记录
            OrderGoods.objects.create(order=order,
                                      sku=sku,
                                      count=count,
                                      price=sku.price)

            # todo: 减少商品的库存，增加销量
            sku.stock -= int(count)
            sku.sales += int(count)
            sku.save()

            # todo: 累加计算用户要购买的商品的总数目和总价格
            total_count += int(count)
            total_price += sku.price * int(count)

        # todo: 更新order对应记录中的total_count和total_price
        order.total_count = total_count
        order.total_price = total_price
        order.save()

        # todo: 删除购物车中对应的记录 sku_ids=[1,2]
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '订单创建成功'})
