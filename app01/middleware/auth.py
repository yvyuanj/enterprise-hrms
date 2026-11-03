"""登录与权限校验。

- AuthMiddleware：未登录访问受保护页面时，自动重定向到登录页（白名单除外）。
- require_permission：接口级权限装饰器，校验当前用户是否拥有指定权限码，
  未授权返回 403。
"""
from django.http import JsonResponse
from django.shortcuts import redirect

# 无需登录即可访问的路径前缀
PUBLIC_PREFIXES = (
    '/login/',
    '/logout/',
    '/captcha/',
    '/static/',
    '/media/',
    '/admin/',
)


class AuthMiddleware:
    """登录拦截中间件：未登录一律跳转登录页。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        # 放行公开路径
        if any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return self.get_response(request)
        # 未登录 -> 登录页
        if not request.user.is_authenticated:
            return redirect('/login/?next=' + path)
        return self.get_response(request)


def require_permission(code):
    """接口级权限校验装饰器。

    用法：@require_permission('employee_add')
    """
    def decorator(view_func):
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/login/?next=' + request.path)
            if not request.user.has_permission(code):
                # 前端 AJAX 请求返回 JSON，普通请求返回 403 页面
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': False, 'error': '没有操作权限'}, status=403)
                return redirect('/403/')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
