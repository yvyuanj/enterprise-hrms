"""用户 / 角色管理（T5 RBAC）。

核心约束：
- 每个登录账号必须关联一名员工（User.employee 非空），保证管理员也在员工列表中；
- 新增账号只能从「尚未开通账号」的员工中选择；
- 删除用户前保护最后一名超级管理员，避免系统失去管理员。
"""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django import forms

from app01 import models
from app01.middleware.auth import require_permission
from app01.utils.pagination import Pagination

User = get_user_model()


class UserCreateForm(forms.Form):
    """新增用户：只能选择尚未开通账号的员工。"""
    employee = forms.ModelChoiceField(label='关联员工', queryset=models.Employee.objects.none())
    username = forms.CharField(label='用户名', max_length=30)
    password = forms.CharField(label='密码', widget=forms.PasswordInput, min_length=6)
    roles = forms.ModelMultipleChoiceField(label='角色', queryset=models.Role.objects.all(),
                                           required=False, widget=forms.CheckboxSelectMultiple)
    is_superuser = forms.BooleanField(label='超级管理员', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 只允许选择未开通账号的员工，严格保证 用户->员工 一对一
        self.fields['employee'].queryset = models.Employee.objects.filter(
            login_user__isnull=True
        )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('用户名已存在')
        return username

    def clean_employee(self):
        employee = self.cleaned_data.get('employee')
        if employee and hasattr(employee, 'login_user'):
            raise forms.ValidationError('该员工已开通账号')
        return employee


class UserEditForm(forms.Form):
    """编辑用户：调整角色 / 管理员标记 / 关联员工。"""
    employee = forms.ModelChoiceField(label='关联员工', queryset=models.Employee.objects.none())
    username = forms.CharField(label='用户名', max_length=30)
    roles = forms.ModelMultipleChoiceField(label='角色', queryset=models.Role.objects.all(),
                                           required=False, widget=forms.CheckboxSelectMultiple)
    is_superuser = forms.BooleanField(label='超级管理员', required=False)

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        # 可关联所有员工（编辑时允许换绑，但目标员工不能已被其他账号占用）
        self.fields['employee'].queryset = models.Employee.objects.all()

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('用户名已存在')
        return username

    def clean_employee(self):
        employee = self.cleaned_data.get('employee')
        if employee and hasattr(employee, 'login_user') and employee.login_user_id != self.instance.pk:
            raise forms.ValidationError('该员工已被其他账号关联')
        return employee


class RoleForm(forms.ModelForm):
    """角色表单。"""

    class Meta:
        model = models.Role
        fields = ['name', 'code', 'permissions']
        widgets = {'permissions': forms.CheckboxSelectMultiple}


@require_permission('user_list')
def user_list(request):
    """用户列表。"""
    queryset = User.objects.select_related('employee__depart').prefetch_related('roles').order_by('id')
    keyword = request.GET.get('kw', '').strip()
    if keyword:
        queryset = queryset.filter(Q(username__icontains=keyword) | Q(employee__name__icontains=keyword))
    pagination = Pagination(queryset, request, 10)
    return render(request, 'user.html', {
        'user_list': pagination.page_queryset,
        'pagination': pagination,
        'kw': keyword,
    })


@require_permission('user_add')
def user_add(request):
    if request.method == 'GET':
        form = UserCreateForm()
        return render(request, 'user_form.html', {'form': form, 'is_edit': False})
    form = UserCreateForm(request.POST)
    if form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
            employee=form.cleaned_data['employee'],
            is_superuser=form.cleaned_data['is_superuser'],
        )
        user.roles.set(form.cleaned_data['roles'])
        return redirect('/user/list/')
    return render(request, 'user_form.html', {'form': form, 'is_edit': False})


@require_permission('user_edit')
def user_edit(request, pk):
    user = User.objects.get(pk=pk)
    if request.method == 'GET':
        form = UserEditForm(instance=user, initial={
            'employee': user.employee_id,
            'username': user.username,
            'roles': user.roles.all(),
            'is_superuser': user.is_superuser,
        })
        return render(request, 'user_form.html', {'form': form, 'is_edit': True, 'user': user})
    form = UserEditForm(request.POST, instance=user)
    if form.is_valid():
        user.username = form.cleaned_data['username']
        user.employee = form.cleaned_data['employee']
        user.is_superuser = form.cleaned_data['is_superuser']
        user.save()
        user.roles.set(form.cleaned_data['roles'])
        return redirect('/user/list/')
    return render(request, 'user_form.html', {'form': form, 'is_edit': True, 'user': user})


@require_permission('user_reset_pwd')
def user_reset_pwd(request, pk):
    """重置密码为 123456。"""
    if request.method != 'POST':
        return JsonResponse({'status': False, 'error': '非法请求'})
    user = User.objects.get(pk=pk)
    user.set_password('123456')
    user.save()
    return JsonResponse({'status': True, 'msg': '密码已重置为 123456'})


@require_permission('user_del')
def user_del(request, pk):
    """删除用户。保护最后一名超级管理员与当前登录账号。"""
    if request.user.pk == pk:
        return JsonResponse({'status': False, 'error': '不能删除当前登录账号'})
    user = User.objects.get(pk=pk)
    if user.is_superuser and not User.objects.filter(is_superuser=True).exclude(pk=pk).exists():
        return JsonResponse({'status': False, 'error': '系统必须保留至少一名超级管理员'})
    user.delete()
    return JsonResponse({'status': True})


# ==================== 角色管理 ====================
@require_permission('role_list')
def role_list(request):
    roles = models.Role.objects.prefetch_related('permissions').order_by('id')
    return render(request, 'role.html', {'role_list': roles})


@require_permission('role_add')
def role_add(request):
    if request.method == 'GET':
        return render(request, 'role_form.html', {'form': RoleForm(), 'is_edit': False})
    form = RoleForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect('/role/list/')
    return render(request, 'role_form.html', {'form': form, 'is_edit': False})


@require_permission('role_edit')
def role_edit(request, pk):
    obj = models.Role.objects.get(pk=pk)
    if request.method == 'GET':
        form = RoleForm(instance=obj)
        return render(request, 'role_form.html', {'form': form, 'is_edit': True})
    form = RoleForm(request.POST, instance=obj)
    if form.is_valid():
        form.save()
        return redirect('/role/list/')
    return render(request, 'role_form.html', {'form': form, 'is_edit': True})


@require_permission('role_del')
def role_del(request, pk):
    """删除角色。若已被用户使用则禁止删除。"""
    obj = models.Role.objects.get(pk=pk)
    if obj.users.exists():
        return JsonResponse({'status': False, 'error': '该角色仍被用户使用，无法删除'})
    obj.delete()
    return JsonResponse({'status': True})
