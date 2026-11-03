"""考勤管理（T6）：CRUD，状态由上下班时间自动计算。"""
from django.http import JsonResponse
from django.shortcuts import redirect, render

from app01 import forms, models
from app01.middleware.auth import require_permission
from app01.utils import rbac
from app01.utils.pagination import Pagination


@require_permission('attendance_list')
def attendance_list(request):
    """考勤列表（支持按员工、日期、状态筛选；按角色限定数据范围）。"""
    queryset = models.Attendance.objects.select_related('employee__depart').order_by('-date')
    # 行级权限
    queryset = rbac.scope_queryset(request, queryset)
    employee_id = request.GET.get('employee', '').strip()
    status = request.GET.get('status', '').strip()
    date = request.GET.get('date', '').strip()
    if employee_id and employee_id.isdigit():
        queryset = queryset.filter(employee_id=employee_id)
    if status and status.isdigit():
        queryset = queryset.filter(status=status)
    if date:
        queryset = queryset.filter(date=date)
    pagination = Pagination(queryset, request, 10)
    return render(request, 'attendance.html', {
        'attendance_list': pagination.page_queryset,
        'pagination': pagination,
        'employee_id': employee_id,
        'status': status,
        'date': date,
        'employee_list': models.Employee.objects.all().order_by('id'),
        'status_choices': models.Attendance.STATUS_CHOICES,
    })


@require_permission('attendance_add')
def attendance_add(request):
    if request.method == 'GET':
        form = forms.AttendanceModelForm()
        return render(request, 'attendance_form.html', {'form': form})
    form = forms.AttendanceModelForm(request.POST)
    if form.is_valid():
        form.save()  # save() 内自动计算 status
        return redirect('/attendance/list/')
    return render(request, 'attendance_form.html', {'form': form})


@require_permission('attendance_edit')
def attendance_edit(request, pk):
    obj = models.Attendance.objects.get(pk=pk)
    if request.method == 'GET':
        form = forms.AttendanceModelForm(instance=obj)
        return render(request, 'attendance_form.html', {'form': form})
    form = forms.AttendanceModelForm(request.POST, instance=obj)
    if form.is_valid():
        form.save()
        return redirect('/attendance/list/')
    return render(request, 'attendance_form.html', {'form': form})


@require_permission('attendance_del')
def attendance_del(request, pk):
    models.Attendance.objects.filter(pk=pk).delete()
    return JsonResponse({'status': True})
