"""公告管理（T8）：发布、列表、置顶、搜索、分页。"""
from django.http import JsonResponse
from django.shortcuts import redirect, render

from app01 import forms, models
from app01.middleware.auth import require_permission
from app01.utils.pagination import Pagination


@require_permission('announcement_list')
def announcement_list(request):
    """公告列表（标题搜索；置顶优先 + 时间倒序）。"""
    queryset = models.Announcement.objects.select_related('publisher').order_by('-is_top', '-create_time')
    keyword = request.GET.get('kw', '').strip()
    if keyword:
        queryset = queryset.filter(title__icontains=keyword)
    pagination = Pagination(queryset, request, 10)
    return render(request, 'announcement.html', {
        'announcement_list': pagination.page_queryset,
        'pagination': pagination,
        'kw': keyword,
    })


@require_permission('announcement_add')
def announcement_add(request):
    if request.method == 'GET':
        form = forms.AnnouncementModelForm()
        return render(request, 'announcement_form.html', {'form': form})
    form = forms.AnnouncementModelForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.publisher = request.user  # 发布人自动取自当前登录用户
        obj.save()
        return redirect('/announcement/list/')
    return render(request, 'announcement_form.html', {'form': form})


@require_permission('announcement_edit')
def announcement_edit(request, pk):
    obj = models.Announcement.objects.get(pk=pk)
    if request.method == 'GET':
        form = forms.AnnouncementModelForm(instance=obj)
        return render(request, 'announcement_form.html', {'form': form})
    form = forms.AnnouncementModelForm(request.POST, instance=obj)
    if form.is_valid():
        form.save()
        return redirect('/announcement/list/')
    return render(request, 'announcement_form.html', {'form': form})


@require_permission('announcement_toggle_top')
def announcement_toggle_top(request, pk):
    """置顶/取消置顶。"""
    obj = models.Announcement.objects.get(pk=pk)
    obj.is_top = not obj.is_top
    obj.save(update_fields=['is_top'])
    return JsonResponse({'status': True, 'is_top': obj.is_top})


@require_permission('announcement_del')
def announcement_del(request, pk):
    models.Announcement.objects.filter(pk=pk).delete()
    return JsonResponse({'status': True})
