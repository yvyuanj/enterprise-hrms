"""文件上传（第20章）：三种上传方式对照。

1. upload_list —— 原始方式：从 request.FILES 拿文件，chunks() 分块写盘；
2. upload_form —— 普通 Form：自己决定存哪、数据库存相对路径（Boss.img 是 CharField）；
3. upload_modal_form —— ModelForm：FileField 自动存到 MEDIA_ROOT/upload_to；
4. tt —— 头像本地预览（FileReader）+ ModelForm 自动保存。
"""
import os

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

from app01 import forms, models
from app01.middleware.auth import require_permission


@require_permission('upload')
def upload_list(request):
    """原始方式上传：文件写到项目根目录（与上传文件名同名）。"""
    if request.method == 'GET':
        return render(request, 'upload_list.html')

    file_object = request.FILES.get('avatar')
    # 参考代码未做判空，这里补上，避免未选文件时抛 AttributeError
    if not file_object:
        return HttpResponse('请先选择文件后再提交')

    with open(os.path.join(settings.BASE_DIR, file_object.name), mode='wb') as f:
        for chunk in file_object.chunks():
            f.write(chunk)
    return HttpResponse(f'上传成功：{file_object.name}')


@require_permission('upload')
def upload_form(request):
    """普通 Form 上传：文件手工写到 media/boss/，数据库只存相对路径。"""
    title = 'Form 上传（Boss）'
    if request.method == 'GET':
        return render(request, 'upload_form.html', {'form': forms.BossForm(), 'title': title, 'back_url': '/upload/form/'})

    form = forms.BossForm(data=request.POST)
    image_object = request.FILES.get('img')
    if not image_object:
        form.add_error(None, '请选择头像文件')
        return render(request, 'upload_form.html', {'form': form, 'title': title})

    if form.is_valid():
        # 1. 确保 media/boss/ 目录存在
        boss_dir = os.path.join(settings.MEDIA_ROOT, 'boss')
        os.makedirs(boss_dir, exist_ok=True)
        # 2. 分块写盘
        with open(os.path.join(boss_dir, image_object.name), mode='wb') as f:
            for chunk in image_object.chunks():
                f.write(chunk)
        # 3. 入库，img 存相对路径，与磁盘位置保持一致
        models.Boss.objects.create(
            name=form.cleaned_data['name'],
            age=form.cleaned_data['age'],
            img='boss/' + image_object.name,
        )
        return HttpResponse('上传成功，已写入 Boss 表')
    return render(request, 'upload_form.html', {'form': form, 'title': title})


@require_permission('upload')
def upload_modal_form(request):
    """ModelForm 上传：FileField 自动保存到 MEDIA_ROOT/city/。"""
    title = 'ModelForm 上传（City）'
    if request.method == 'GET':
        return render(request, 'upload_form.html', {'form': forms.CityModelForm(), 'title': title})

    form = forms.CityModelForm(data=request.POST, files=request.FILES)
    if form.is_valid():
        form.save()   # 文件自动落到 media/city/，路径写入数据库
        return HttpResponse('上传成功，已写入 City 表')
    return render(request, 'upload_form.html', {'form': form, 'title': title})


@require_permission('upload')
def tt(request):
    """头像预览：FileReader 只在浏览器本地预览，真正上传靠表单提交。"""
    if request.method == 'GET':
        return render(request, 'tt.html', {'form': forms.XXModelForm()})

    form = forms.XXModelForm(data=request.POST, files=request.FILES)
    if form.is_valid():
        form.save()
    return render(request, 'tt.html', {'form': form})

