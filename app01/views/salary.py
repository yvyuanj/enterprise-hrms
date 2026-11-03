"""薪资管理（T7）：实发自动计算、按月份/员工筛选、选定月份总额统计。"""
from decimal import Decimal

from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render

from app01 import forms, models
from app01.middleware.auth import require_permission
from app01.utils import rbac
from app01.utils.pagination import Pagination


@require_permission('salary_list')
def salary_list(request):
    """薪资列表 + 总额统计（按角色限定数据范围）。"""
    queryset = models.Salary.objects.select_related('employee__depart').order_by('-month')
    # 行级权限
    queryset = rbac.scope_queryset(request, queryset)
    month = request.GET.get('month', '').strip()
    employee_id = request.GET.get('employee', '').strip()
    if month:
        queryset = queryset.filter(month=month)
    if employee_id and employee_id.isdigit():
        queryset = queryset.filter(employee_id=employee_id)

    # 选定月份的薪资总额统计（BasicTotal / BonusTotal / DeductionTotal / RealTotal）
    stat = {
        'count': queryset.count(),
        'basic': queryset.aggregate(t=Sum('basic'))['t'] or Decimal('0.00'),
        'bonus': queryset.aggregate(t=Sum('bonus'))['t'] or Decimal('0.00'),
        'deduction': queryset.aggregate(t=Sum('deduction'))['t'] or Decimal('0.00'),
        'total': queryset.aggregate(t=Sum('total'))['t'] or Decimal('0.00'),
    }
    pagination = Pagination(queryset, request, 10)
    return render(request, 'salary.html', {
        'salary_list': pagination.page_queryset,
        'pagination': pagination,
        'month': month,
        'employee_id': employee_id,
        'stat': stat,
        'employee_list': models.Employee.objects.all().order_by('id'),
    })


@require_permission('salary_add')
def salary_add(request):
    if request.method == 'GET':
        form = forms.SalaryModelForm()
        return render(request, 'salary_form.html', {'form': form})
    form = forms.SalaryModelForm(request.POST)
    if form.is_valid():
        form.save()  # save() 内自动计算实发
        return redirect('/salary/list/')
    return render(request, 'salary_form.html', {'form': form})


@require_permission('salary_edit')
def salary_edit(request, pk):
    obj = models.Salary.objects.get(pk=pk)
    if request.method == 'GET':
        form = forms.SalaryModelForm(instance=obj)
        return render(request, 'salary_form.html', {'form': form})
    form = forms.SalaryModelForm(request.POST, instance=obj)
    if form.is_valid():
        form.save()
        return redirect('/salary/list/')
    return render(request, 'salary_form.html', {'form': form})


@require_permission('salary_del')
def salary_del(request, pk):
    models.Salary.objects.filter(pk=pk).delete()
    return JsonResponse({'status': True})
