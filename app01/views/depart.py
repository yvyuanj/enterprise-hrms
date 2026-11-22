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


@require_permission('depart_add')
def depart_multi(request):
    """批量导入部门（Excel 文件）。

    要点：
    - 文件在 request.FILES 里，不在 request.POST；
    - openpyxl 可直接读取 UploadedFile 这种类文件对象，无需先存盘；
    - 第一行视为标题行，从第 2 行开始取第 1 列；
    - 已存在的部门名不重复插入（幂等）。
    """
    from openpyxl import load_workbook

    # 1. 取用户上传的文件对象
    file_object = request.FILES.get('exc')
    if not file_object:
        return render(request, 'depart.html', {
            'error': '请选择要上传的 Excel 文件（.xlsx）',
            **_depart_page_context(request),
        })

    # 2. 交给 openpyxl 解析（只读工作簿第一个 sheet）
    try:
        wb = load_workbook(file_object, read_only=True)
        sheet = wb.worksheets[0]
    except Exception:
        return render(request, 'depart.html', {
            'error': '文件无法解析，请确认是 .xlsx 格式的 Excel 文件',
            **_depart_page_context(request),
        })

    # 3. 逐行取第 1 列，做去空、去重后入库
    created = 0
    skipped = 0
    for row in sheet.iter_rows(min_row=2, max_col=1, values_only=True):
        text = (str(row[0]).strip() if row[0] is not None else '')
        if not text:
            skipped += 1
            continue
        obj, is_new = models.Department.objects.get_or_create(name=text)
        created += 1 if is_new else 0
        skipped += 0 if is_new else 1

    return render(request, 'depart.html', {
        'success': f'导入完成：新增 {created} 个部门，跳过重复/空行 {skipped} 条',
        **_depart_page_context(request),
    })


def _depart_page_context(request):
    """部门列表页的公共上下文（列表/分页/搜索词），供普通渲染与导入回显复用。"""
    queryset = models.Department.objects.all().order_by('id')
    keyword = request.GET.get('kw', '').strip()
    if keyword:
        queryset = queryset.filter(name__icontains=keyword)
    pagination = Pagination(queryset, request, 10)
    return {
        'depart_list': pagination.page_queryset,
        'pagination': pagination,
        'kw': keyword,
    }
