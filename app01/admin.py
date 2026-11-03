"""Django admin 后台注册（供演示，主要功能在自定义前端完成）。"""
from django.contrib import admin

from app01 import models

admin.site.register(models.Department)
admin.site.register(models.Employee)
admin.site.register(models.Permission)
admin.site.register(models.Role)
admin.site.register(models.Attendance)
admin.site.register(models.Salary)
admin.site.register(models.Announcement)
admin.site.register(models.Task)
