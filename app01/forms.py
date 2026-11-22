"""表单与校验。

ModelForm 集中承担数据校验，保证新增与编辑场景口径一致：
- 员工：姓名长度、年龄范围、手机号正则 + 唯一（编辑时排除自身）；
- 考勤：状态由上下班时间自动计算；
- 薪资：实发自动计算（基本工资 + 奖金 - 扣款）。
"""
import re

from django import forms
from django.core.exceptions import ValidationError

from app01 import models


class DepartmentModelForm(forms.ModelForm):
    """部门表单。"""

    class Meta:
        model = models.Department
        fields = ['name']
        error_messages = {
            'name': {'required': '部门名称不能为空', 'unique': '部门名称已存在'},
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise ValidationError('部门名称不能为空')
        return name


class EmployeeModelForm(forms.ModelForm):
    """员工表单：含姓名、年龄、手机号校验。"""

    class Meta:
        model = models.Employee
        fields = ['name', 'age', 'gender', 'account', 'hire_date', 'phone',
                  'depart', 'avatar']
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(),
        }
        error_messages = {
            'name': {'required': '姓名不能为空'},
            'age': {'required': '年龄不能为空'},
            'phone': {'required': '手机号不能为空'},
            'depart': {'required': '请选择所属部门'},
        }

    def __init__(self, *args, **kwargs):
        # 编辑场景下需排除自身的手机号唯一性判断
        self.instance_pk = kwargs.pop('instance_pk', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) > 16:
            raise ValidationError('姓名长度不能超过16个字符')
        if len(name) < 1:
            raise ValidationError('姓名不能为空')
        return name

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is None:
            raise ValidationError('年龄不能为空')
        if not 18 <= age <= 65:
            raise ValidationError('年龄必须在18-65岁之间')
        return age

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise ValidationError('手机号不能为空')
        if not re.match(r'^1[3-9]\d{9}$', phone):
            raise ValidationError('手机号格式不正确（需为 1 开头的 11 位号码）')
        qs = models.Employee.objects.filter(phone=phone)
        if self.instance_pk:
            qs = qs.exclude(pk=self.instance_pk)
        if qs.exists():
            raise ValidationError('该手机号已被其他员工使用')
        return phone


class AttendanceModelForm(forms.ModelForm):
    """考勤表单：状态字段不出现在表单中，由上下班时间自动计算。"""

    class Meta:
        model = models.Attendance
        fields = ['employee', 'date', 'check_in', 'check_out']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'check_in': forms.TimeInput(attrs={'type': 'time'}),
            'check_out': forms.TimeInput(attrs={'type': 'time'}),
        }
        error_messages = {
            'employee': {'required': '请选择员工'},
            'date': {'required': '请选择日期'},
            'check_in': {'required': '请选择上班时间'},
            'check_out': {'required': '请选择下班时间'},
        }

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get('check_in')
        check_out = cleaned.get('check_out')
        if check_in and check_out and check_out <= check_in:
            raise ValidationError('下班时间必须晚于上班时间')
        return cleaned


class SalaryModelForm(forms.ModelForm):
    """薪资表单：实发在保存时自动计算，表单中不展示 total。"""

    class Meta:
        model = models.Salary
        fields = ['employee', 'month', 'basic', 'bonus', 'deduction']
        widgets = {
            'month': forms.TextInput(attrs={'placeholder': '格式：2026-11'}),
        }
        error_messages = {
            'employee': {'required': '请选择员工'},
            'month': {'required': '请输入月份'},
            'basic': {'required': '请输入基本工资'},
        }

    def clean_month(self):
        month = self.cleaned_data.get('month')
        if month and not re.match(r'^\d{4}-(0[1-9]|1[0-2])$', month):
            raise ValidationError('月份格式不正确（应为 YYYY-MM，如 2026-11）')
        return month

    def clean_basic(self):
        basic = self.cleaned_data.get('basic')
        if basic is not None and basic < 0:
            raise ValidationError('基本工资不能为负数')
        return basic

    def clean_deduction(self):
        deduction = self.cleaned_data.get('deduction')
        if deduction is not None and deduction < 0:
            raise ValidationError('扣款不能为负数')
        return deduction


class AnnouncementModelForm(forms.ModelForm):
    """公告表单。"""

    class Meta:
        model = models.Announcement
        fields = ['title', 'content', 'is_top']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }
        error_messages = {
            'title': {'required': '标题不能为空'},
            'content': {'required': '内容不能为空'},
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title) > 64:
            raise ValidationError('标题长度不能超过64个字符')
        return title


class TaskModelForm(forms.ModelForm):
    """任务表单（AJAX 异步提交）。"""

    class Meta:
        model = models.Task
        fields = ['level', 'title', 'detail', 'owner']
        error_messages = {
            'level': {'required': '请选择级别'},
            'title': {'required': '标题不能为空'},
            'detail': {'required': '详情不能为空'},
            'owner': {'required': '请选择负责人'},
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title) > 64:
            raise ValidationError('标题长度不能超过64个字符')
        return title


class OrderModelForm(forms.ModelForm):
    """订单表单（第18章）。

    exclude 掉 oid（订单号）与 admin（管理员）：
    这两个字段由后端自动生成，不能开放给用户修改。
    """

    class Meta:
        model = models.Order
        fields = ['title', 'price', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'title': {'required': '名称不能为空'},
            'price': {'required': '价格不能为空'},
            'status': {'required': '请选择状态'},
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title) > 32:
            raise ValidationError('名称长度不能超过32个字符')
        return title

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError('价格不能为负数')
        return price


class BossForm(forms.ModelForm):
    """老板表单（第20.2章：普通 Form 方式，文件由视图手工写盘）。

    img 不是 Boss 的模型字段（模型里是 CharField 存路径），
    这里单独声明一个 FileField，只为在页面上出现文件选择框。
    """

    img = forms.FileField(label='头像', required=False)

    class Meta:
        model = models.Boss
        fields = ['name', 'age']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 文件框单独在模板里渲染，这里只给文本字段套上 bootstrap 样式
        for name, field in self.fields.items():
            if name == 'img':
                continue
            field.widget.attrs.setdefault('class', 'form-control')


class CityModelForm(forms.ModelForm):
    """城市表单（第21章：ModelForm + FileField，文件自动保存）。"""

    class Meta:
        model = models.City
        fields = ['name', 'count', 'img']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            # 文件框不套 form-control，否则 Bootstrap 会把它渲染成文本框样式
            if name == 'img':
                continue
            field.widget.attrs.setdefault('class', 'form-control')


class XXModelForm(forms.ModelForm):
    """头像示例表单（第20.4章）。"""

    class Meta:
        model = models.XX
        fields = ['title', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'image':
                continue
            field.widget.attrs.setdefault('class', 'form-control')
