"""核心流程单元测试（T12 选做）。

覆盖：登录与验证码、权限拦截、员工表单校验、考勤状态自动计算、
薪资实发自动计算、管理员必须在员工列表内。
运行：python manage.py test app01
"""
from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase

from app01 import forms, models

User = get_user_model()


class BaseSetup(TestCase):
    """公共初始化。"""

    def setUp(self):
        self.depart = models.Department.objects.create(name='技术部')
        self.employee = models.Employee.objects.create(
            name='张伟', age=28, gender=1, account=0,
            hire_date=date(2020, 1, 1), phone='13800000000', depart=self.depart,
        )
        self.permission = models.Permission.objects.create(code='employee_list', name='查看员工')
        self.role = models.Role.objects.create(name='普通员工', code='employee')
        self.role.permissions.add(self.permission)
        # 管理员：先建员工，再建账号并关联
        self.admin_employee = models.Employee.objects.create(
            name='系统管理员', age=30, gender=3, account=0,
            hire_date=date(2019, 1, 1), phone='13900000000', depart=self.depart,
        )
        self.admin = User.objects.create_user(
            username='admin', password='123456',
            employee=self.admin_employee, is_superuser=True,
        )
        self.user = User.objects.create_user(
            username='zhangwei', password='123456', employee=self.employee,
        )
        self.user.roles.add(self.role)


class AttendanceStatusTests(BaseSetup):
    """考勤状态自动计算。"""

    def test_on_time(self):
        a = models.Attendance(employee=self.employee, date=date(2026, 11, 1),
                              check_in=time(9, 0), check_out=time(18, 0))
        self.assertEqual(a.compute_status(), 1)  # 按时

    def test_late(self):
        a = models.Attendance(employee=self.employee, date=date(2026, 11, 1),
                              check_in=time(9, 30), check_out=time(18, 0))
        self.assertEqual(a.compute_status(), 2)  # 迟到

    def test_early(self):
        a = models.Attendance(employee=self.employee, date=date(2026, 11, 1),
                              check_in=time(8, 50), check_out=time(17, 30))
        self.assertEqual(a.compute_status(), 3)  # 早退

    def test_missing(self):
        a = models.Attendance(employee=self.employee, date=date(2026, 11, 1),
                              check_in=None, check_out=time(18, 0))
        self.assertEqual(a.compute_status(), 4)  # 缺勤


class SalaryTotalTests(BaseSetup):
    """薪资实发自动计算。"""

    def test_total_formula(self):
        # 构造薪资记录：基本工资 8000、奖金 1000、扣款 500
        s = models.Salary(employee=self.employee, month='2026-11',
                          basic=8000, bonus=1000, deduction=500)
        s.save()  # 保存时触发实发工资自动计算
        # 实发 = 基本工资 + 奖金 - 扣款 = 8500
        self.assertEqual(s.total, 8500)

    def test_total_negative_deduction_large(self):
        # 构造薪资记录：基本工资 5000、无奖金、扣款 6000（大于基本工资）
        s = models.Salary(employee=self.employee, month='2026-10',
                          basic=5000, bonus=0, deduction=6000)
        s.save()  # 保存时触发实发工资自动计算
        # 实发 = 5000 + 0 - 6000 = -1000，验证扣款超额时允许为负数
        self.assertEqual(s.total, -1000)


class EmployeeFormTests(BaseSetup):
    """员工表单校验。"""

    def test_invalid_phone_rejected(self):
        form = forms.EmployeeModelForm(data={
            'name': '测试', 'age': 25, 'gender': 1, 'account': 0,
            'hire_date': date(2021, 1, 1), 'phone': '12345',
            'depart': self.depart.id,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_duplicate_phone_rejected(self):
        form = forms.EmployeeModelForm(data={
            'name': '测试', 'age': 25, 'gender': 1, 'account': 0,
            'hire_date': date(2021, 1, 1), 'phone': '13800000000',
            'depart': self.depart.id,
        })
        self.assertFalse(form.is_valid())

    def test_edit_excludes_self_phone(self):
        form = forms.EmployeeModelForm(
            instance=self.employee, instance_pk=self.employee.pk,
            data={
                'name': '张伟', 'age': 29, 'gender': 1, 'account': 0,
                'hire_date': date(2020, 1, 1), 'phone': '13800000000',
                'depart': self.depart.id,
            },
        )
        self.assertTrue(form.is_valid())

    def test_age_out_of_range_rejected(self):
        form = forms.EmployeeModelForm(data={
            'name': '测试', 'age': 17, 'gender': 1, 'account': 0,
            'hire_date': date(2021, 1, 1), 'phone': '13700000000',
            'depart': self.depart.id,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('age', form.errors)


class AuthPermissionTests(BaseSetup):
    """登录拦截与权限。"""

    def test_unauthenticated_redirect_to_login(self):
        resp = self.client.get('/employee/list/')
        self.assertRedirects(resp, '/login/?next=/employee/list/')

    def test_login_success(self):
        session = self.client.session
        session['captcha_code'] = 'abcd'
        session.save()
        resp = self.client.post('/login/', {
            'username': 'admin', 'password': '123456', 'captcha': 'abcd',
        })
        self.assertEqual(resp.status_code, 302)

    def test_login_wrong_captcha(self):
        session = self.client.session
        session['captcha_code'] = 'abcd'
        session.save()
        resp = self.client.post('/login/', {
            'username': 'admin', 'password': '123456', 'captcha': 'wrong',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '验证码错误')

    def test_permission_blocked(self):
        """普通员工访问无权限的功能应被拒绝。"""
        self.client.login(username='zhangwei', password='123456')
        # 普通员工无 depart_del 权限 -> 重定向到 403
        resp = self.client.get('/depart/list/')
        self.assertRedirects(resp, '/403/')

    def test_superuser_access_ok(self):
        self.client.login(username='admin', password='123456')
        resp = self.client.get('/depart/list/')
        self.assertEqual(resp.status_code, 200)

    def test_admin_is_in_employee_list(self):
        """管理员必须同时是员工列表中的一员。"""
        self.assertTrue(hasattr(self.admin, 'employee'))
        self.assertTrue(hasattr(self.admin.employee, 'login_user'))
        self.assertEqual(self.admin.employee, self.admin_employee)
