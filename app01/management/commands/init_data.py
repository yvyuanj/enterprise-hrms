"""初始化基础数据：权限、角色、超级管理员。

用法：python manage.py init_data

设计要点：
- 权限点（RBAC 最小单元）一次性创建，供角色勾选与接口校验；
- 超级管理员也「先建员工、再建账号」，且账号通过 User.employee 一对一关联该员工，
  从而保证管理员一定出现在员工列表中（符合任务要求「管理员必须是员工列表里面的」）。
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from app01 import models

User = get_user_model()

# 全部权限点：模块_动作
ALL_PERMISSIONS = [
    ('index', '访问首页'),

    ('depart_list', '查看部门'), ('depart_add', '新增部门'),
    ('depart_edit', '编辑部门'), ('depart_del', '删除部门'),

    ('employee_list', '查看员工'), ('employee_add', '新增员工'),
    ('employee_edit', '编辑员工'), ('employee_del', '删除员工'),

    ('attendance_list', '查看考勤'), ('attendance_add', '新增考勤'),
    ('attendance_edit', '编辑考勤'), ('attendance_del', '删除考勤'),

    ('salary_list', '查看薪资'), ('salary_add', '新增薪资'),
    ('salary_edit', '编辑薪资'), ('salary_del', '删除薪资'),

    ('announcement_list', '查看公告'), ('announcement_add', '发布公告'),
    ('announcement_edit', '编辑公告'), ('announcement_del', '删除公告'),
    ('announcement_toggle_top', '公告置顶'),

    ('task_list', '查看任务'), ('task_add', '新增任务'), ('task_del', '删除任务'),

    ('user_list', '查看用户'), ('user_add', '新增用户'),
    ('user_edit', '编辑用户'), ('user_del', '删除用户'),
    ('user_reset_pwd', '重置密码'),

    ('role_list', '查看角色'), ('role_add', '新增角色'),
    ('role_edit', '编辑角色'), ('role_del', '删除角色'),

    ('chart', '数据统计'),
]

# 角色 -> 权限编码
ROLES = {
    '超级管理员': {
        'code': 'super',
        'permissions': [p for p, _ in ALL_PERMISSIONS],
    },
    '部门管理员': {
        'code': 'depart_admin',
        'permissions': [
            'index',
            'depart_list',
            'employee_list', 'employee_add', 'employee_edit',
            'attendance_list', 'attendance_add', 'attendance_edit',
            'salary_list', 'salary_add', 'salary_edit',
            'announcement_list',
            'task_list', 'task_add',
        ],
    },
    '普通员工': {
        'code': 'employee',
        'permissions': [
            'index',
            'employee_list',
            'attendance_list',
            'salary_list',
            'announcement_list',
            'task_list',
        ],
    },
}

# 管理员账号
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '123456'
ADMIN_EMPLOYEE_NAME = '系统管理员'


class Command(BaseCommand):
    help = '初始化权限、角色与超级管理员账号（可重复执行）'

    def handle(self, *args, **options):
        # 1. 权限点
        for code, name in ALL_PERMISSIONS:
            models.Permission.objects.get_or_create(code=code, defaults={'name': name})
        self.stdout.write(self.style.SUCCESS(f'[1/4] 权限点就绪：{len(ALL_PERMISSIONS)} 项'))

        # 2. 角色
        perm_map = {p.code: p for p in models.Permission.objects.all()}
        for role_name, cfg in ROLES.items():
            role, _ = models.Role.objects.get_or_create(
                code=cfg['code'], defaults={'name': role_name}
            )
            role.permissions.set([perm_map[c] for c in cfg['permissions'] if c in perm_map])
        self.stdout.write(self.style.SUCCESS(f'[2/4] 角色就绪：{list(ROLES)}'))

        # 3. 管理员员工（先建员工，保证管理员在员工列表内）
        depart = models.Department.objects.first()
        if not depart:
            depart = models.Department.objects.create(name='综合管理部')
        admin_employee, created = models.Employee.objects.get_or_create(
            name=ADMIN_EMPLOYEE_NAME,
            defaults={'age': 30, 'gender': 3, 'account': 0,
                      'hire_date': '2020-01-01', 'phone': '13900000000',
                      'depart': depart},
        )

        # 4. 管理员账号（关联该员工）
        if User.objects.filter(username=ADMIN_USERNAME).exists():
            user = User.objects.get(username=ADMIN_USERNAME)
            user.employee = admin_employee
            user.is_superuser = True
            user.set_password(ADMIN_PASSWORD)
            user.save()
        else:
            user = User.objects.create_user(
                username=ADMIN_USERNAME, password=ADMIN_PASSWORD,
                employee=admin_employee, is_superuser=True,
            )
        super_role = models.Role.objects.get(code='super')
        user.roles.set([super_role])

        self.stdout.write(self.style.SUCCESS(
            f'[3/4] 管理员账号就绪：{ADMIN_USERNAME} / {ADMIN_PASSWORD}'
            f'（关联员工「{admin_employee.name}」，已在员工列表中）'
        ))
        self.stdout.write(self.style.SUCCESS('[4/4] 初始化完成。'))
