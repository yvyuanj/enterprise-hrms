"""任务管理（T9）：AJAX 异步提交 + JSON 回显校验错误，不刷新页面。"""
from django.http import JsonResponse
from django.shortcuts import render

from app01 import forms, models
from app01.middleware.auth import require_permission


@require_permission('task_list')
def task_list(request):
    """任务列表（GET 渲染页面，列表数据含于页面）。"""
    queryset = models.Task.objects.select_related('owner').order_by('-create_time')
    return render(request, 'task.html', {
        'task_list': queryset[:100],
        'form': forms.TaskModelForm(),
    })


@require_permission('task_add')
def task_add(request):
    """AJAX 新增任务：提交成功后返回 JSON，前端不刷新页面。"""
    if request.method == 'GET':
        return JsonResponse({'status': False, 'error': '非法请求'})

    form = forms.TaskModelForm(request.POST)
    if form.is_valid():
        obj = form.save()
        return JsonResponse({
            'status': True,
            'data': {
                'id': obj.id,
                'level': obj.get_level_display(),
                'title': obj.title,
                'detail': obj.detail,
                'owner': obj.owner.name,
                'create_time': obj.create_time.strftime('%Y-%m-%d %H:%M'),
            }
        })
    # 返回校验错误，供前端回显到表单字段
    errors = {}
    for field, errs in form.errors.items():
        errors[field] = errs[0]
    return JsonResponse({'status': False, 'errors': errors})


@require_permission('task_del')
def task_del(request, pk):
    models.Task.objects.filter(pk=pk).delete()
    return JsonResponse({'status': True})
