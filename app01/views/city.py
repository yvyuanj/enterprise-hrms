"""城市列表（第21章）：FileField + MEDIA_ROOT。

FileField 数据库只存相对路径（city/xx.png），
真实文件在 settings.MEDIA_ROOT 下，通过 /media/ 前缀访问（路由见 hrms/urls.py）。
"""
from django.shortcuts import redirect, render

from app01 import forms, models
from app01.middleware.auth import require_permission


@require_permission('city_list')
def city_list(request):
    """城市列表（带 Logo 缩略图）。"""
    queryset = models.City.objects.all().order_by('id')
    return render(request, 'city_list.html', {'queryset': queryset})


@require_permission('city_add')
def city_add(request):
    """新建城市：ModelForm 自动把上传图片存到 media/city/。"""
    title = '新建城市'
    if request.method == 'GET':
        return render(request, 'upload_form.html',
                      {'form': forms.CityModelForm(), 'title': title, 'back_url': '/city/list/'})

    form = forms.CityModelForm(data=request.POST, files=request.FILES)
    if form.is_valid():
        form.save()
        return redirect('/city/list/')
    return render(request, 'upload_form.html', {'form': form, 'title': title})

