"""项目配置包。"""

try:
    import pymysql

    # 使用 PyMySQL 作为 MySQL 驱动，兼容 Django 的 mysql 后端。
    # 若未安装 PyMySQL 且使用 SQLite 时，可安全跳过。
    pymysql.install_as_MySQLdb()
except ImportError:  # pragma: no cover
    pass
