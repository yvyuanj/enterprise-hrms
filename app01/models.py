"""数据模型。

设计要点（逻辑严谨性）：
1. 自定义用户模型 User 继承 AbstractUser，并通过「一对一」关联到员工 Employee；
   User.employee 为必填，因此任何登录账号（包括超级管理员）必然对应一名员工，
   从而严格满足「管理员必须是员工列表里面的」这一约束。
2. Employee 关联 Department；Employee 被删除时若有登录账号则受 PROTECT 保护。
3. 考勤状态、实发工资均由系统自动计算，不交给前端/用户手工填写。
"""
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Department(models.Model):
    """部门。"""
    name = models.CharField('部门名称', max_length=32, unique=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'hr_department'
        verbose_name = '部门'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name


class Permission(models.Model):
    """权限点（RBAC 的最小单位）。code 形如 'employee_add'。"""
    code = models.CharField('权限编码', max_length=64, unique=True)
    name = models.CharField('权限名称', max_length=32)

    class Meta:
        db_table = 'hr_permission'
        verbose_name = '权限'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.name}({self.code})'


class Role(models.Model):
    """角色，与权限多对多。"""
    name = models.CharField('角色名称', max_length=32, unique=True)
    code = models.CharField('角色编码', max_length=32, unique=True)
    permissions = models.ManyToManyField(
        Permission, verbose_name='权限', blank=True, related_name='roles'
    )

    class Meta:
        db_table = 'hr_role'
        verbose_name = '角色'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Employee(models.Model):
    """员工档案。"""

    GENDER_CHOICES = ((1, '男'), (2, '女'), (3, '保密'))

    name = models.CharField('姓名', max_length=16)
    age = models.IntegerField('年龄')
    gender = models.SmallIntegerField('性别', choices=GENDER_CHOICES, default=3)
    account = models.DecimalField('账户余额', max_digits=10, decimal_places=2,
                                  default=Decimal('0.00'))
    hire_date = models.DateField('入职时间')
    phone = models.CharField('手机号', max_length=11, unique=True)
    depart = models.ForeignKey(
        Department, on_delete=models.PROTECT, verbose_name='所属部门',
        related_name='employees'
    )
    avatar = models.ImageField('头像', upload_to='avatars/', null=True, blank=True)

    class Meta:
        db_table = 'hr_employee'
        verbose_name = '员工'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name

    @property
    def has_account(self):
        """是否已经开通登录账号（是否有员工被 User 关联）。"""
        return hasattr(self, 'login_user')


class User(AbstractUser):
    """自定义用户模型。

    employee 为必填的一对一关联：每个登录账号都必须对应一名员工。
    这是「管理员（及任何用户）都必须是员工列表中的一员」的硬约束。
    """
    employee = models.OneToOneField(
        Employee, on_delete=models.PROTECT, verbose_name='关联员工',
        related_name='login_user'
    )
    roles = models.ManyToManyField(
        Role, verbose_name='角色', blank=True, related_name='users'
    )

    class Meta:
        db_table = 'hr_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def has_permission(self, code):
        """判断当前用户是否拥有某权限码（超级管理员默认拥有全部）。

        按请求缓存权限码集合，避免模板中多次 check_perm 造成重复查询。
        """
        if self.is_superuser:
            return True
        if not hasattr(self, '_perm_cache'):
            self._perm_cache = set(
                self.roles.values_list('permissions__code', flat=True)
            )
        return code in self._perm_cache

    @property
    def role_names(self):
        return '、'.join(self.roles.values_list('name', flat=True)) or '无角色'


class Attendance(models.Model):
    """考勤记录。状态由上下班时间自动计算。"""

    STATUS_CHOICES = (
        (1, '按时'),
        (2, '迟到'),
        (3, '早退'),
        (4, '缺勤'),
    )
    # 公司标准上下班时间（可在此统一调整）
    WORK_START = timezone.datetime.strptime('09:00', '%H:%M').time()
    WORK_END = timezone.datetime.strptime('18:00', '%H:%M').time()

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, verbose_name='员工',
        related_name='attendances'
    )
    date = models.DateField('日期')
    check_in = models.TimeField('上班时间')
    check_out = models.TimeField('下班时间')
    status = models.SmallIntegerField('考勤状态', choices=STATUS_CHOICES, editable=False)

    class Meta:
        db_table = 'hr_attendance'
        verbose_name = '考勤'
        verbose_name_plural = verbose_name
        unique_together = ('employee', 'date')  # 同一员工同一天仅一条考勤
        ordering = ['-date']

    def __str__(self):
        return f'{self.employee.name} {self.date}'

    def compute_status(self):
        """按上下班时间自动判定考勤状态。

        规则（优先级从高到低）：
        1. 缺勤：上班或下班任一时间缺失；
        2. 迟到：上班时间晚于标准上班时间；
        3. 早退：下班时间早于标准下班时间；
        4. 按时：其余情况（不迟到、不早退、不缺勤）。
        """
        def to_time(value):
            """把字符串时间（如 '09:05'）转为 time 对象，保证计算健壮。"""
            if isinstance(value, str):
                try:
                    parts = value.split(':')
                    return timezone.datetime.strptime(
                        f'{int(parts[0]):02d}:{int(parts[1]):02d}', '%H:%M').time()
                except (ValueError, IndexError):
                    return None
            return value

        check_in = to_time(self.check_in)
        check_out = to_time(self.check_out)
        if not check_in or not check_out:
            return 4
        late = check_in > self.WORK_START
        early = check_out < self.WORK_END
        if late:
            return 2
        if early:
            return 3
        return 1

    def save(self, *args, **kwargs):
        # 状态一律自动计算，防止前后端不一致
        self.status = self.compute_status()
        super().save(*args, **kwargs)


class Salary(models.Model):
    """薪资记录。实发 = 基本工资 + 奖金 - 扣款，系统自动计算。"""

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, verbose_name='员工',
        related_name='salaries'
    )
    month = models.CharField('月份', max_length=7)  # 格式 YYYY-MM
    basic = models.DecimalField('基本工资', max_digits=10, decimal_places=2,
                                default=Decimal('0.00'))
    bonus = models.DecimalField('奖金', max_digits=10, decimal_places=2,
                                default=Decimal('0.00'))
    deduction = models.DecimalField('扣款', max_digits=10, decimal_places=2,
                                    default=Decimal('0.00'))
    total = models.DecimalField('实发', max_digits=10, decimal_places=2,
                                default=Decimal('0.00'), editable=False)

    class Meta:
        db_table = 'hr_salary'
        verbose_name = '薪资'
        verbose_name_plural = verbose_name
        unique_together = ('employee', 'month')
        ordering = ['-month', 'id']

    def __str__(self):
        return f'{self.employee.name} {self.month}'

    def save(self, *args, **kwargs):
        # 实发自动计算：实发 = 基本工资 + 奖金 - 扣款
        self.total = self.basic + self.bonus - self.deduction
        super().save(*args, **kwargs)


class Announcement(models.Model):
    """公告。"""

    title = models.CharField('标题', max_length=64)
    content = models.TextField('内容')
    publisher = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name='发布人',
        related_name='announcements'
    )
    create_time = models.DateTimeField('发布时间', auto_now_add=True)
    is_top = models.BooleanField('置顶', default=False)

    class Meta:
        db_table = 'hr_announcement'
        verbose_name = '公告'
        verbose_name_plural = verbose_name
        ordering = ['-is_top', '-create_time']

    def __str__(self):
        return self.title


class Task(models.Model):
    """任务（使用 AJAX 异步提交）。"""

    LEVEL_CHOICES = (
        (1, '低'),
        (2, '中'),
        (3, '高'),
    )

    level = models.SmallIntegerField('级别', choices=LEVEL_CHOICES, default=2)
    title = models.CharField('标题', max_length=64)
    detail = models.TextField('详情')
    owner = models.ForeignKey(
        Employee, on_delete=models.PROTECT, verbose_name='负责人',
        related_name='tasks'
    )
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'hr_task'
        verbose_name = '任务'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return self.title
