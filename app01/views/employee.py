"""员工管理（T3）：CRUD + 姓名搜索 + 部门筛选 + 分页 + 头像上传。"""
from django.http import JsonResponse
from django.shortcuts import redirect, render

from app01 import forms, models
from app01.middleware.auth import require_permission
from app01.utils import rbac
from app01.utils.pagination import Pagination


def _base_queryset(request):
    """按搜索/筛选条件构造查询集，并应用角色行级数据范围。"""
    queryset = models.Employee.objects.select_related('depart').order_by('id')
    # 行级权限：超级管理员看全部，部门管理员看本部门，普通员工仅看本人
    kind, value = rbac.get_scope(request)
    if kind == 'employee':
        queryset = queryset.filter(pk=value)
    elif kind == 'depart':
        queryset = queryset.filter(depart_id=value)
    keyword = request.GET.get('kw', '').strip()
    depart_id = request.GET.get('depart', '').strip()
    if keyword:
        queryset = queryset.filter(name__icontains=keyword)
    if depart_id and depart_id.isdigit():
        queryset = queryset.filter(depart_id=depart_id)
    return queryset, keyword, depart_id


@require_permission('employee_list')
def employee_list(request):
    """员工列表。"""
    queryset, keyword, depart_id = _base_queryset(request)
    pagination = Pagination(queryset, request, 10)
    return render(request, 'employee.html', {
        'employee_list': pagination.page_queryset,
        'pagination': pagination,
        'kw': keyword,
        'depart_id': depart_id,
        'depart_list': models.Department.objects.all().order_by('id'),
    })


@require_permission('employee_add')
def employee_add(request):
    """新增员工。"""
    if request.method == 'GET':
        form = forms.EmployeeModelForm()
        return render(request, 'employee_form.html', {'form': form})
    form = forms.EmployeeModelForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        return redirect('/employee/list/')
    return render(request, 'employee_form.html', {'form': form})


@require_permission('employee_edit')
def employee_edit(request, pk):
    """编辑员工（手机号唯一性排除自身）。"""
    obj = models.Employee.objects.get(pk=pk)
    if request.method == 'GET':
        form = forms.EmployeeModelForm(instance=obj)
        return render(request, 'employee_form.html', {'form': form})
    form = forms.EmployeeModelForm(request.POST, request.FILES, instance=obj,
                                   instance_pk=pk)
    if form.is_valid():
        form.save()
        return redirect('/employee/list/')
    return render(request, 'employee_form.html', {'form': form})


@require_permission('employee_del')
def employee_del(request, pk):
    """删除员工。若该员工已开通登录账号（如管理员），则禁止删除以保数据完整。"""
    obj = models.Employee.objects.get(pk=pk)
    if hasattr(obj, 'login_user'):
        return JsonResponse({'status': False, 'error': '该员工已开通登录账号，请先删除其账号'})
    obj.delete()
    return JsonResponse({'status': True})
