# 企业员工管理系统（HRMS）

基于 Django 5.2 的企业员工管理系统课程设计。覆盖：部门、员工、登录认证（含图片验证码）、
RBAC 权限、考勤、薪资、公告、任务（AJAX）、数据统计可视化。

## 技术栈

| 项 | 说明 |
|----|------|
| 后端 | Django 5.2（MTV） |
| 数据库 | MySQL（默认）；可一键切换 SQLite 快速体验 |
| 前端 | Bootstrap 3.4.1 + jQuery 3.6.0 + ECharts（均已内置到 `static/plugins`，离线可用） |
| 认证 | 自定义用户模型 `app01.User`（继承 `AbstractUser`），密码 Django 安全哈希 |
| 权限 | RBAC（用户 - 角色 - 权限），含数据行级作用域（普通员工仅本人、部门管理员本部门） |

## 目录结构

```
hrms/
├── manage.py
├── requirements.txt
├── hrms/                    # 项目配置（settings / urls / wsgi / asgi）
└── app01/                   # 业务应用
    ├── models.py            # 数据模型
    ├── forms.py             # 表单校验
    ├── views/               # 视图（按模块拆分）
    ├── middleware/          # 登录拦截 + 接口权限装饰器
    ├── templatetags/        # 前端权限隐藏按钮等模板标签
    ├── utils/               # 分页 / 验证码 / 行级权限
    ├── management/commands/ # init_data / demo_data 初始化命令
    ├── tests.py             # 单元测试
    ├── templates/           # 模板
    └── static/              # 静态资源（含离线第三方库）
```

## 快速开始

### 1. 环境准备

```bash
# 建议使用虚拟环境
python -m venv venv
# Windows: venv\Scripts\activate    Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

### 2. 数据库

- **默认 MySQL**：在 MySQL 中创建数据库，例如 `CREATE DATABASE hrms DEFAULT CHARSET utf8mb4;`
  再通过环境变量配置连接信息：

```bash
# Windows (PowerShell)
$env:DB_NAME='hrms'; $env:DB_USER='root'; $env:DB_PASSWORD='你的密码'
# Linux/macOS
export DB_NAME=hrms DB_USER=root DB_PASSWORD='你的密码'
```

- **快速体验（无需 MySQL）**：设置环境变量 `DB_ENGINE=sqlite` 即可使用 SQLite。

### 3. 初始化

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py init_data     # 权限 / 角色 / 超级管理员（管理员也是员工列表中的一员）
python manage.py demo_data     # 可选：演示数据 + 示例账号
python manage.py runserver     # http://127.0.0.1:8000/index/
```

### 4. 内置账号

| 账号 | 密码 | 角色 | 说明 |
|------|------|------|------|
| `admin` | `123456` | 超级管理员 | 关联员工「系统管理员」，出现在员工列表中 |
| `dept_admin` | `123456` | 部门管理员 | 示例账号（demo_data 生成，张伟） |
| `emp01` | `123456` | 普通员工 | 示例账号（demo_data 生成，王芳） |

## 功能清单（对应任务书）

- **T1 环境与项目初始化**：MySQL 配置、`zh-hans`、`AUTH_USER_MODEL`、`requirements.txt`
- **T2 部门管理**：新增 / 查询 / 编辑 / 删除（列表表格 + 操作按钮）
- **T3 员工管理**：ModelForm 校验（姓名长度、年龄范围、手机号正则唯一）、搜索 / 筛选 / 分页 / 头像上传
- **T4 登录认证**：图片验证码（点击刷新）、安全哈希密码、会话、未登录跳转
- **T5 权限控制（RBAC）**：角色 - 权限多对多；中间件拦截 + 装饰器接口校验 + 前端按权限隐藏按钮
- **T6 考勤管理**：状态由上下班时间自动计算（按时 / 迟到 / 早退 / 缺勤）
- **T7 薪资管理**：实发 = 基本工资 + 奖金 - 扣款（自动计算）、按月份 / 员工筛选、总额统计
- **T8 公告管理**：发布 / 列表 / 置顶 / 搜索 / 分页
- **T9 任务管理（AJAX）**：异步提交 + JSON 返回 + 校验错误实时回显，不刷新页面
- **T10 数据统计（选做）**：ECharts 部门人数分布、各月薪资趋势（AJAX 取数）
- **T11 性能（选做）**：列表页 `select_related` / `prefetch_related` 消除 N+1
- **T12 测试（选做）**：`python manage.py test app01`
- **T13 安全（选做）**：支持关闭 `DEBUG`、`ALLOWED_HOSTS`、会话有效期

## 逻辑严谨性说明

1. **管理员必须在员工列表中**：自定义用户模型 `User` 与员工 `Employee` 一对一关联（`User.employee`
   必填）。新增账号只能从「尚未开通账号」的员工中选择，因此任何登录账号（含超级管理员）都必然
   对应一条员工档案。
2. **考勤状态 / 实发工资不人工填写**：由模型 `save()` 统一自动计算，杜绝前后端不一致。
3. **删除保护**：部门下有员工不可删；已开通账号的员工不可直接删；角色被用户使用不可删；
   系统至少保留一名超级管理员。
4. **行级数据权限**：普通员工仅看本人，部门管理员仅看本部门（`utils/rbac.py`）。
