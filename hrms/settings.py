"""Django 项目全局配置。"""
import os
from pathlib import Path

# ============ 基础路径 ============
BASE_DIR = Path(__file__).resolve().parent.parent

# ============ 密钥与调试 ============
# 生产环境务必修改并通过环境变量注入，且将 DEBUG 置为 False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-hrms-course-design-change-me')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# ============ 应用注册 ============
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app01',  # 业务应用
]

# ============ 中间件 ============
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 自定义：登录与接口级权限校验
    'app01.middleware.auth.AuthMiddleware',
]

ROOT_URLCONF = 'hrms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            # 自动加载 templatetags 模块中的自定义标签
            'builtins': ['app01.templatetags.hrms_tags'],
        },
    },
]

WSGI_APPLICATION = 'hrms.wsgi.application'

# ============ 数据库 ============
# 按任务书要求默认使用 MySQL；可通过环境变量 DB_ENGINE=sqlite 快速切换为 SQLite 体验。
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'hrms'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
if os.environ.get('DB_ENGINE') == 'sqlite':
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

# ============ 密码与认证 ============
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
]
# 自定义用户模型（继承 AbstractUser）
AUTH_USER_MODEL = 'app01.User'

LOGIN_URL = '/login/'

# ============ 国际化 ============
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = False  # 关闭 UTC，直接使用本地时间，方便课程设计展示

# ============ 静态资源与媒体 ============
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'app01' / 'static']
STATIC_ROOT = BASE_DIR / 'static_collected'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============ 会话有效期（24 小时） ============
SESSION_COOKIE_AGE = 60 * 60 * 24
