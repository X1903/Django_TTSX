from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.views.generic import View
from django.db import transaction

from apps.user.models import Address
from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods

from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from datetime import datetime


from alipay import AliPay
import os
from GitHub_TTSX import settings


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
# 悲观锁代码
class OrderCommitView1(View):
    """订单创建"""
    @transaction.atomic
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

        # todo: 设置事务保存点
        sid = transaction.savepoint()

        try:
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
            cart_key = 'cart_%d'%user.id
            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                # 获取商品的信息
                try:
                    # select * from df_goods_sku where id=sku_id;
                    # sku = GoodsSKU.objects.get(id=sku_id)
                    # select * from df_goods_sku where id=sku_id for update;
                    print('user:%d try get lock'%user.id)
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                    print('user:%d get lock'%user.id)
                except GoodsSKU.DoesNotExist:
                    # 商品不存在，回滚到sid事务保存点
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                # 获取用户要购买商品的数量
                count = conn.hget(cart_key, sku_id)

                # 判断商品的库存
                if int(count) > sku.stock:
                    # 商品库存不足，回滚到sid事务保存点
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                import time
                time.sleep(10)

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
                total_price += sku.price*int(count)

            # todo: 更新order对应记录中的total_count和total_price
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            # 数据库操作出错，回滚到sid事务保存点
            transaction.savepoint_rollback(sid)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        # todo: 删除购物车中对应的记录 sku_ids=[1,2]
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '订单创建成功'})




# /order/commit
# 前端采用ajax post请求
# 传递的参数：收货地址id(addr_id) 支付方式(pay_method) 用户要购买商品id(sku_ids) 1,2,3
# 乐观锁代码
class OrderCommitView(View):
    """订单创建"""
    @transaction.atomic
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

        # todo: 设置事务保存点
        sid = transaction.savepoint()

        try:
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
            cart_key = 'cart_%d'%user.id
            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                for i in range(3):
                    # 获取商品的信息
                    try:
                        # select * from df_goods_sku where id=sku_id;
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        # 商品不存在，回滚到sid事务保存点
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                    # 获取用户要购买商品的数量
                    count = conn.hget(cart_key, sku_id)

                    # 判断商品的库存
                    if int(count) > sku.stock:
                        # 商品库存不足，回滚到sid事务保存点
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                    # todo: 减少商品的库存，增加销量

                    origin_stock = sku.stock
                    new_stock = origin_stock - int(count)
                    new_sales = sku.sales + int(count)

                    # print('user:%d times:%d origin_stock:%d'%(user.id, i, origin_stock))
                    # import time
                    # time.sleep(10)

                    # update from df_goods_sku set stock=new_stock,sales=new_sales
                    # where id=sku_id and stock=origin_stock;
                    # update返回的是更新的行数
                    res = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                    if res == 0:
                        # 更新失败
                        if i == 2:
                            # 尝试3次之后仍然更新失败，下单失败
                            transaction.savepoint_rollback(sid)
                            return JsonResponse({'res': 7, 'errmsg': '下单失败2'})
                        continue

                    # todo: 向df_order_goods中添加一条记录
                    OrderGoods.objects.create(order=order,
                                              sku=sku,
                                              count=count,
                                              price=sku.price)

                    # todo: 累加计算用户要购买的商品的总数目和总价格
                    total_count += int(count)
                    total_price += sku.price*int(count)

                    # 更新成功则跳出循环
                    break

            # todo: 更新order对应记录中的total_count和total_price
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            # 数据库操作出错，回滚到sid事务保存点
            transaction.savepoint_rollback(sid)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        # todo: 删除购物车中对应的记录 sku_ids=[1,2]
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '订单创建成功'})




# /order/pay
# 前端采用ajax post请求
# 传递的参数： 订单id(orde_id)
class OrderPayView(View):
    """订单支付"""
    def post(self, request):
        """订单支付"""
        # 用户登录校验
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 参数校验
        if not all([order_id]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验订单id
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1
                                      )
        except OrderInfo.DoesNotExist as e:
            print('_+' * 20)
            print(e)
            return JsonResponse({'res': 2, 'errmsg': '订单信息错误'})


        # 业务处理：调用支付宝下单支付接口
        # 初始化
        alipay = AliPay(
            appid="2016091100487438", # 应用APPID
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'), # 网站私钥文件的路径
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'), # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )

        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        total_amount = order.total_price + order.transit_price # Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id, # 订单id
            total_amount=str(total_amount), # 订单总金额
            subject='天天生鲜%s'%order_id, # 订单标题
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )
        # 返回应答
        pay_url = "https://openapi.alipaydev.com/gateway.do?" + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# /order/check
# 前端采用ajax post请求
# 传递的参数： 订单id(orde_id)
class CheckPayView(View):
    """支付结果查询"""
    def post(self, request):
        """支付结果查询"""
        # 用户登录校验
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 参数校验
        if not all([order_id]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验订单id
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1
                                          )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单信息错误'})

        # 业务处理：调用支付宝交易查询接口
        # 初始化
        alipay = AliPay(
            appid="2016091100487438",  # 应用APPID
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),  # 网站私钥文件的路径
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )

        # 调用支付宝交易查询的api函数
        # {
        #         "trade_no": "2017032121001004070200176844", # 支付宝交易号
        #         "code": "10000", # 网关的返回码
        #         "invoice_amount": "20.00",
        #         "open_id": "20880072506750308812798160715407",
        #         "fund_bill_list": [
        #             {
        #                 "amount": "20.00",
        #                 "fund_channel": "ALIPAYACCOUNT"
        #             }
        #         ],
        #         "buyer_logon_id": "csq***@sandbox.com",
        #         "send_pay_date": "2017-03-21 13:29:17",
        #         "receipt_amount": "20.00",
        #         "out_trade_no": "out_trade_no15",
        #         "buyer_pay_amount": "20.00",
        #         "buyer_user_id": "2088102169481075",
        #         "msg": "Success",
        #         "point_amount": "0.00",
        #         "trade_status": "TRADE_SUCCESS", # 支付交易状态
        #         "total_amount": "20.00"
        # }

        while True:
            response = alipay.api_alipay_trade_query(out_trade_no=order_id)
            # 获取网关返回码
            code = response.get('code')
            print(code)

            if code == '10000' and response.get('trade_status') == "TRADE_SUCCESS":
                # 用户支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')

                # 更新订单的状态，填写支付宝交易号
                print("*"*30)
                order.order_status = 4 # 待评价
                order.trade_no = trade_no
                order.save()

                # 返回应答
                return JsonResponse({'res': 3, 'message': '支付成功'})
            elif code == '40004' or (code == '10000' and response.get('trade_status') == "WAIT_BUYER_PAY"):
                # 等待买家付款
                # 支付交易还未创建成功
                import time
                time.sleep(5)
                continue
            else:
                # 支付失败
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})



# /order/comment/订单id
class OrderCommentView(LoginRequiredMixin, View):
    """订单评论"""
    def get(self, request, order_id):
        """显示"""
        # 获取登录用户
        user = request.user
        # 获取订单信息
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            # 订单信息不存在，跳转到用户订单页面
            return redirect(reverse('user:order', kwargs={'page':1}))

        # 获取订单的支付状态名称
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 获取订单商品的信息
        order_skus = OrderGoods.objects.filter(order=order)

        # 遍历计算订单商品的小计
        for order_sku in order_skus:
            # 计算小计
            amount = order_sku.price*order_sku.count
            # 给order_sku增加属性amount，保存商品的小计
            order_sku.amount = amount

        # 计算订单的实付款
        order.total_amount = order.total_price + order.transit_price

        # 给order增加属性order_skus，保存订单商品的信息
        order.order_skus = order_skus

        # 组织模板上下文
        context = {'order':order}

        # 使用模板
        return render(request, 'order_comment.html', context)

    def post(self, request, order_id):
        """评论处理"""
        # 获取登录用户
        user = request.user

        # 获取订单信息
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            # 订单信息不存在，跳转到用户订单页面
            return redirect(reverse('user:order', kwargs={'page': 1}))

        # todo: 获取待评论商品数目
        count = request.POST.get('count') # 2
        try:
            count = int(count)
        except Exception as e:
            # 数据非法
            return redirect(reverse('user:order', kwargs={'page': 1}))

        # todo: 遍历获取商品的评论信息
        for i in range(1, count+1):
            # 获取第i的商品的id
            sku_id = request.POST.get('sku_%d'%i) # sku_1 sku_2
            print(sku_id)
            # 获取商品的信息
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except Exception as e:
                print(e)
                continue

            # 获取订单商品的信息
            try:
                order_sku = OrderGoods.objects.get(order=order,
                                                   sku=sku)
            except Exception as e:
                # 用户没有购买过该商品，不能评论
                print(e)
                continue

            # 获取对应商品的评论内容
            comment = request.POST.get('content_%d'%i) # content_1 content_2
            print(comment)

            # 设置订单商品的评论
            order_sku.comment = comment
            order_sku.save()

        # todo: 更新订单的状态
        order.order_status = 5 # 已完成
        order.save()

        # 返回应答，跳转到用户订单页面
        return redirect(reverse('user:order', kwargs={'page': 1}))