"""RBAC 数据行级作用域。

根据当前用户角色，确定其可见的数据范围，用于列表查询：
- 超级管理员：全部数据；
- 部门管理员：本部门数据；
- 普通员工：仅本人数据。
"""
from app01 import models

# 约定的角色编码
ROLE_SUPER = 'super'
ROLE_DEPART_ADMIN = 'depart_admin'
ROLE_EMPLOYEE = 'employee'


def get_scope(request):
    """返回当前用户的数据范围。

    返回：(kind, value)
      ('all', None)        全部
      ('employee', id)     仅本人（员工 id）
      ('depart', id)       本部门（部门 id）
    """
    user = request.user
    if user.is_superuser:
        return ('all', None)
    role_codes = set(user.roles.values_list('code', flat=True))
    if ROLE_DEPART_ADMIN in role_codes:
        return ('depart', user.employee.depart_id)
    if ROLE_EMPLOYEE in role_codes:
        return ('employee', user.employee_id)
    return ('all', None)


def scope_queryset(request, queryset, employee_field='employee'):
    """按数据范围过滤查询集。

    employee_field 为查询集上的员工外键字段名，默认为 'employee'。
    """
    kind, value = get_scope(request)
    if kind == 'employee':
        return queryset.filter(**{f'{employee_field}_id': value})
    if kind == 'depart':
        return queryset.filter(**{f'{employee_field}__depart_id': value})
    return queryset
