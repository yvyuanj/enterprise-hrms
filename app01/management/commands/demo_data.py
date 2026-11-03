"""写入演示数据，便于各阶段自测与界面展示。

用法：python manage.py init_data && python manage.py demo_data

本命令依赖 init_data 已创建角色（super / depart_admin / employee）。
"""
import random
from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from app01 import models

User = get_user_model()

DEPARTMENTS = ['技术部', '市场部', '财务部', '人事部', '销售部']

# (姓名, 部门名)
EMPLOYEES = [
    ('张伟', '技术部'), ('王芳', '技术部'), ('李娜', '技术部'), ('刘洋', '技术部'),
    ('陈静', '市场部'), ('杨帆', '市场部'), ('赵磊', '市场部'),
    ('黄敏', '财务部'), ('周涛', '财务部'),
    ('吴倩', '人事部'), ('徐强', '人事部'),
    ('孙丽', '销售部'), ('马超', '销售部'), ('朱琳', '销售部'), ('胡军', '销售部'),
]

MONTHS = ['2026-08', '2026-09', '2026-10', '2026-11']


class Command(BaseCommand):
    help = '写入演示数据（部门/员工/考勤/薪资/公告/任务及示例账号）'

    def handle(self, *args, **options):
        # 部门
        depart_map = {}
        for name in DEPARTMENTS:
            d, _ = models.Department.objects.get_or_create(name=name)
            depart_map[name] = d

        # 员工（手机号保证唯一）
        phone_base = 13800000000
        emp_list = []
        for idx, (name, dname) in enumerate(EMPLOYEES):
            emp, created = models.Employee.objects.get_or_create(
                phone=str(phone_base + idx),
                defaults={
                    'name': name, 'age': random.randint(24, 45),
                    'gender': random.choice([1, 1, 2, 2, 3]),
                    'account': round(random.uniform(1000, 20000), 2),
                    'hire_date': date(random.randint(2018, 2025), random.randint(1, 12),
                                      random.randint(1, 28)),
                    'depart': depart_map[dname],
                },
            )
            emp_list.append(emp)
        self.stdout.write(self.style.SUCCESS(f'[1/5] 部门 {len(depart_map)} 个，员工 {len(emp_list)} 名'))

        # 考勤：最近 10 个工作日，随机上下班时间
        def workdays(end, n):
            days, cur = [], end
            while len(days) < n:
                if cur.weekday() < 5:
                    days.append(cur)
                cur -= timedelta(days=1)
            return days

        attend_days = workdays(date.today(), 10)
        for emp in emp_list:
            for d in attend_days:
                if random.random() < 0.12:
                    continue  # 偶发缺卡
                check_in = datetime.strptime('08:45', '%H:%M').time() \
                    if random.random() < 0.7 else datetime.strptime('09:05', '%H:%M').time()
                check_out = datetime.strptime('18:05', '%H:%M').time() \
                    if random.random() < 0.75 else datetime.strptime('17:50', '%H:%M').time()
                models.Attendance.objects.get_or_create(
                    employee=emp, date=d,
                    defaults={'check_in': check_in, 'check_out': check_out},
                )
        self.stdout.write(self.style.SUCCESS(f'[2/5] 考勤记录写入（近 {len(attend_days)} 个工作日）'))

        # 薪资
        for emp in emp_list:
            for m in MONTHS:
                basic = random.choice([6000, 7000, 8000, 9000, 10000])
                bonus = round(random.uniform(0, 2000), 2)
                deduction = round(random.uniform(0, 800), 2)
                models.Salary.objects.get_or_create(
                    employee=emp, month=m,
                    defaults={'basic': basic, 'bonus': bonus, 'deduction': deduction},
                )
        self.stdout.write(self.style.SUCCESS(f'[3/5] 薪资记录 {len(emp_list) * len(MONTHS)} 条'))

        # 公告
        admin = User.objects.filter(is_superuser=True).first()
        publisher = admin or User.objects.first()
        announcements = [
            ('关于 2026 年度员工体检的通知', '请全体员工于本月内到指定医院完成年度体检，体检费用由公司承担。'),
            ('国庆假期值班安排', '国庆期间各部门需安排值班人员，请于 9 月 25 日前提交值班表。'),
            ('新版员工管理系统上线', '系统已支持考勤、薪资、公告、任务管理，欢迎使用。'),
        ]
        for i, (title, content) in enumerate(announcements):
            models.Announcement.objects.get_or_create(
                title=title,
                defaults={'content': content, 'publisher': publisher,
                          'is_top': (i == 0)},
            )
        self.stdout.write(self.style.SUCCESS(f'[4/5] 公告 {len(announcements)} 条'))

        # 任务
        for i, title in enumerate(['优化登录页验证码', '整理三季度考勤数据', '设计薪资报表模板']):
            models.Task.objects.get_or_create(
                title=title,
                defaults={'level': random.choice([1, 2, 3]),
                          'detail': f'{title}：请在两周内完成，负责人需按时提交。',
                          'owner': random.choice(emp_list)},
            )
        self.stdout.write(self.style.SUCCESS('[5/5] 任务写入完成'))

        # 示例账号：部门管理员 + 普通员工（均关联到员工列表）
        super_role = models.Role.objects.get(code='super')
        depart_admin_role = models.Role.objects.get(code='depart_admin')
        employee_role = models.Role.objects.get(code='employee')

        dept_admin_emp = emp_list[0]  # 张伟（技术部）
        u1, created = User.objects.get_or_create(
            username='dept_admin',
            defaults={'employee': dept_admin_emp},
        )
        u1.employee = dept_admin_emp
        u1.set_password('123456')
        u1.save()
        u1.roles.set([depart_admin_role])
        if not created:
            u1.roles.set([depart_admin_role])

        emp_demo = emp_list[1]  # 王芳
        u2, created = User.objects.get_or_create(
            username='emp01',
            defaults={'employee': emp_demo},
        )
        u2.employee = emp_demo
        u2.set_password('123456')
        u2.save()
        u2.roles.set([employee_role])

        self.stdout.write(self.style.SUCCESS(
            '示例账号：dept_admin / 123456（部门管理员·张伟）；'
            'emp01 / 123456（普通员工·王芳）'
        ))
        self.stdout.write(self.style.SUCCESS('演示数据写入完成。'))
