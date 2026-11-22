"""订单管理（第18章）：列表分页 + Ajax 新增/编辑/删除/详情。

与参考代码的差异（已按本项目规范适配）：
1. 不用 `@csrf_exempt`：layout.html 里已全局给 Ajax 带上 CSRF Token；
2. 不用 `request.session["info"]["id"]`：本项目用 Django 认证，直接取 request.user；
3. Order.admin 关联自定义 User，而 User 又强制对应一名员工，
   所以「下单管理员」一定来自员工列表。
"""
import random
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import render

from app01 import forms, models
from app01.middleware.auth import require_permission
from app01.utils.pagination import Pagination


def _errors_to_dict(form):
    """把 form.errors 摊平成 {字段: 第一条错误}，方便前端按字段回显。"""
    return {field: errs[0] for field, errs in form.errors.items()}


@require_permission('order_list')
def order_list(request):
    """订单列表（分页）。"""
    queryset = models.Order.objects.select_related('admin').order_by('-id')
    page_object = Pagination(queryset, request, 10)
    return render(request, 'order_list.html', {
        'form': forms.OrderModelForm(),
        'queryset': page_object.page_queryset,
        'page_string': page_object.page_html(),
    })


@require_permission('order_add')
def order_add(request):
    """Ajax 新建订单：订单号后端生成，管理员取当前登录用户。"""
    if request.method == 'GET':
        return JsonResponse({'status': False, 'error': '非法请求'})

    form = forms.OrderModelForm(data=request.POST)
    if form.is_valid():
        # 订单号 = 时间戳 + 4 位随机数，保证基本不重复
        form.instance.oid = datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(1000, 9999))
        form.instance.admin = request.user
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': _errors_to_dict(form)})


@require_permission('order_del')
def order_delete(request):
    """删除订单。"""
    uid = request.GET.get('uid')
    if not models.Order.objects.filter(id=uid).exists():
        return JsonResponse({'status': False, 'error': '删除失败，数据不存在。'})
    models.Order.objects.filter(id=uid).delete()
    return JsonResponse({'status': True})


@require_permission('order_edit')
def order_detail(request):
    """按 ID 取订单详情，用于编辑弹窗回填。"""
    uid = request.GET.get('uid')
    row = models.Order.objects.filter(id=uid).values('title', 'price', 'status').first()
    if not row:
        return JsonResponse({'status': False, 'error': '数据不存在。'})
    return JsonResponse({'status': True, 'data': row})


@require_permission('order_edit')
def order_edit(request):
    """编辑订单（只允许改名称/价格/状态，订单号与管理员不变）。"""
    uid = request.GET.get('uid')
    row = models.Order.objects.filter(id=uid).first()
    if not row:
        return JsonResponse({'status': False, 'tips': '数据不存在，请刷新重试。'})

    form = forms.OrderModelForm(data=request.POST, instance=row)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': _errors_to_dict(form)})
