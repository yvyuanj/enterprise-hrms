"""模板标签：前端按权限隐藏按钮、常用显示过滤器。

在 settings 中已把本模块注册为 builtins，模板中可直接使用，无需 {% load %}。
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# ============ 权限判断 ============
@register.filter
def has_perm(user, code):
    """判断当前登录用户是否拥有某权限，用于前端隐藏按钮。

    用法：{% if request.user|has_perm:'employee_add' %}...{% endif %}
    """
    return user.has_permission(code)


# ============ 状态/标签显示 ============
@register.filter
def gender_label(value):
    return dict(((1, '男'), (2, '女'), (3, '保密'))).get(value, '未知')


@register.filter
def status_badge(value, status_type='attendance'):
    """把状态值渲染为彩色标签。"""
    if status_type == 'attendance':
        table = {
            1: ('success', '按时'), 2: ('warning', '迟到'),
            3: ('danger', '早退'), 4: ('secondary', '缺勤'),
        }
    elif status_type == 'task':
        table = {
            1: ('info', '低'), 2: ('warning', '中'), 3: ('danger', '高'),
        }
    else:
        table = {}
    css, label = table.get(value, ('secondary', '未知'))
    return mark_safe(f'<span class="label label-{css}">{label}</span>')


@register.filter
def top_badge(value):
    """置顶公告标徽。"""
    if value:
        return mark_safe('<span class="label label-danger">置顶</span>')
    return ''


@register.filter
def money(value):
    """金额格式化：保留两位小数。"""
    try:
        return f'{float(value):,.2f}'
    except (TypeError, ValueError):
        return value


@register.filter
def avatar_url(employee):
    """头像 URL：无头像时使用默认占位图。"""
    if employee and employee.avatar:
        return employee.avatar.url
    return '/static/img/default-avatar.png'
