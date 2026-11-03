"""首页（统计 + 快捷入口）与数据统计可视化（T10）。"""
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import render

from app01 import models
from app01.middleware.auth import require_permission


@require_permission('index')
def index(request):
    """首页：四个统计卡片 + 快捷入口 + 最新公告。"""
    context = {
        'depart_count': models.Department.objects.count(),
        'employee_count': models.Employee.objects.count(),
        'announcement_count': models.Announcement.objects.count(),
        'salary_count': models.Salary.objects.count(),
        'announcements': models.Announcement.objects.select_related('publisher')
                         .order_by('-is_top', '-create_time')[:5],
    }
    return render(request, 'index.html', context)


@require_permission('chart')
def chart(request):
    """数据统计页：部门人数分布 + 各月薪资趋势。"""
    return render(request, 'chart.html')


@require_permission('chart')
def depart_data(request):
    """AJAX：各部门员工人数。"""
    rows = (models.Employee.objects.values('depart__name')
            .annotate(count=Count('id')).order_by('-count'))
    return JsonResponse({'status': True, 'data': list(rows)})


@require_permission('chart')
def salary_trend(request):
    """AJAX：各月薪资总额趋势（含基本工资与实发）。"""
    rows = (models.Salary.objects.values('month')
            .annotate(
                basic=Sum('basic'),
                total=Sum('total'),
            ).order_by('month'))
    data = [{
        'month': r['month'],
        'basic': float(r['basic'] or 0),
        'total': float(r['total'] or 0),
    } for r in rows]
    return JsonResponse({'status': True, 'data': data})
