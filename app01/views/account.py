"""登录 / 注销 / 验证码。"""
from django.contrib import auth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from app01.utils.captcha import build_captcha_image, gen_code_text


def captcha(request):
    """生成图片验证码并写入 session。"""
    code = gen_code_text(4)
    request.session['captcha_code'] = code.lower()
    image_bytes = build_captcha_image(code)
    return HttpResponse(image_bytes, content_type='image/png')


def login(request):
    """登录：校验验证码 + 用户名密码。"""
    if request.user.is_authenticated:
        return redirect('/index/')

    if request.method == 'GET':
        return render(request, 'login.html')

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    captcha_input = request.POST.get('captcha', '').strip().lower()
    session_captcha = request.session.get('captcha_code', '')

    # 校验验证码
    if not captcha_input or captcha_input != session_captcha:
        return render(request, 'login.html',
                      {'error': '验证码错误', 'username': username})
    # 校验账号密码
    user = auth.authenticate(request, username=username, password=password)
    if not user or not user.is_active:
        return render(request, 'login.html',
                      {'error': '用户名或密码错误', 'username': username})

    auth.login(request, user)
    next_url = request.GET.get('next', '/index/')
    return redirect(next_url)


def logout(request):
    """注销并跳转登录页。"""
    auth.logout(request)
    return redirect('/login/')


def forbidden(request):
    """403 无权限页面。"""
    return render(request, 'error.html', {'code': 403, 'message': '没有操作权限'})
