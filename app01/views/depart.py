"""部门管理（T2）。"""
from django.http import JsonResponse
from django.shortcuts import redirect, render

from app01 import forms, models
from app01.middleware.auth import require_permission
from app01.utils.pagination import Pagination


@require_permission('depart_list')
def depart_list(request):
    """部门列表（支持名称模糊搜索 + 分页）。"""
    queryset = models.Department.objects.all().order_by('id')
    keyword = request.GET.get('kw', '').strip()
    if keyword:
        queryset = queryset.filter(name__icontains=keyword)
    pagination = Pagination(queryset, request, 10)
    return render(request, 'depart.html', {
        'depart_list': pagination.page_queryset,
        'pagination': pagination,
        'kw': keyword,
    })


@require_permission('depart_add')
def depart_add(request):
    """新增部门。"""
    if request.method == 'GET':
        return render(request, 'depart_form.html', {'form': forms.DepartmentModelForm()})
    form = forms.DepartmentModelForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect('/depart/list/')
    return render(request, 'depart_form.html', {'form': form, 'errors': form.errors})


@require_permission('depart_edit')
def depart_edit(request, pk):
    """编辑部门。"""
    obj = models.Department.objects.get(pk=pk)
    if request.method == 'GET':
        form = forms.DepartmentModelForm(instance=obj)
        return render(request, 'depart_form.html', {'form': form})
    form = forms.DepartmentModelForm(request.POST, instance=obj)
    if form.is_valid():
        form.save()
        return redirect('/depart/list/')
    return render(request, 'depart_form.html', {'form': form, 'errors': form.errors})


@require_permission('depart_del')
def depart_del(request, pk):
    """删除部门。若部门下仍有员工则禁止删除（PROTECT 保证）。"""
    obj = models.Department.objects.get(pk=pk)
    if obj.employees.exists():
        return JsonResponse({'status': False, 'error': '该部门下仍有员工，无法删除'})
    obj.delete()
    return JsonResponse({'status': True})
