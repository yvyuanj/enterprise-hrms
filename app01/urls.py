"""app01 路由。"""
from django.urls import path

from app01.views import account, announcement, attendance, dashboard, depart
from app01.views import employee, salary, task, user

urlpatterns = [
    # 首页 / 可视化
    path('index/', dashboard.index),
    path('chart/', dashboard.chart),
    path('chart/depart-data/', dashboard.depart_data),
    path('chart/salary-trend/', dashboard.salary_trend),

    # 认证
    path('login/', account.login),
    path('logout/', account.logout),
    path('captcha/', account.captcha),
    path('403/', account.forbidden),

    # 部门
    path('depart/list/', depart.depart_list),
    path('depart/add/', depart.depart_add),
    path('depart/edit/<int:pk>/', depart.depart_edit),
    path('depart/del/<int:pk>/', depart.depart_del),

    # 员工
    path('employee/list/', employee.employee_list),
    path('employee/add/', employee.employee_add),
    path('employee/edit/<int:pk>/', employee.employee_edit),
    path('employee/del/<int:pk>/', employee.employee_del),

    # 考勤
    path('attendance/list/', attendance.attendance_list),
    path('attendance/add/', attendance.attendance_add),
    path('attendance/edit/<int:pk>/', attendance.attendance_edit),
    path('attendance/del/<int:pk>/', attendance.attendance_del),

    # 薪资
    path('salary/list/', salary.salary_list),
    path('salary/add/', salary.salary_add),
    path('salary/edit/<int:pk>/', salary.salary_edit),
    path('salary/del/<int:pk>/', salary.salary_del),

    # 公告
    path('announcement/list/', announcement.announcement_list),
    path('announcement/add/', announcement.announcement_add),
    path('announcement/edit/<int:pk>/', announcement.announcement_edit),
    path('announcement/toggle-top/<int:pk>/', announcement.announcement_toggle_top),
    path('announcement/del/<int:pk>/', announcement.announcement_del),

    # 任务（AJAX）
    path('task/list/', task.task_list),
    path('task/add/', task.task_add),
    path('task/del/<int:pk>/', task.task_del),

    # 用户 / 角色
    path('user/list/', user.user_list),
    path('user/add/', user.user_add),
    path('user/edit/<int:pk>/', user.user_edit),
    path('user/reset-pwd/<int:pk>/', user.user_reset_pwd),
    path('user/del/<int:pk>/', user.user_del),
    path('role/list/', user.role_list),
    path('role/add/', user.role_add),
    path('role/edit/<int:pk>/', user.role_edit),
    path('role/del/<int:pk>/', user.role_del),
]
