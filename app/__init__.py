"""
Flask 应用工厂模块
负责创建和配置 Flask 应用实例，注册所有扩展和蓝图
"""
from datetime import timedelta
from functools import wraps

from flask import Flask, flash, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# PyMySQL 仅在 MySQL 模式下需要
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# 初始化扩展（暂未绑定到具体 app 实例）
db = SQLAlchemy()             # 数据库 ORM
login_manager = LoginManager() # 用户登录管理
migrate = Migrate()           # 数据库迁移
csrf = CSRFProtect()          # CSRF 保护
bootstrap = Bootstrap5()      # Bootstrap5 支持


def permission_required(permission):
    """
    权限拦截装饰器
    用法: @permission_required('user:manage')
    如果未登录则跳转登录页；如果已登录但无权限则提示并返回首页
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('请先登录后再进行此操作', 'warning')
                return redirect(url_for('auth.login', next=url_for('main.index')))
            if not current_user.has_permission(permission):
                flash('权限不足，请联系管理员', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def _seed_admin():
    """首次启动时自动创建管理员账号（如果数据库为空）"""
    from app.models import Role, User
    if User.query.first() is not None:
        return  # 已有用户，跳过

    import json
    # 创建管理员角色（拥有所有权限）
    all_perms = [
        'user:manage', 'role:manage', 'room:view', 'room:manage',
        'room_type:manage', 'order:view', 'order:create', 'order:cancel',
        'order:checkin', 'order:checkout', 'credit:view', 'credit:manage',
        'stats:view', 'review:view', 'review:manage',
    ]
    admin_role = Role(role_name='管理员', permissions=json.dumps(all_perms))
    db.session.add(admin_role)
    db.session.flush()

    # 创建默认管理员
    admin = User(username='admin', name='管理员', role_id=admin_role.id)
    admin.password = 'admin123'
    db.session.add(admin)
    db.session.commit()
    print('✅ 已创建默认管理员: admin / admin123')


def create_app():
    """创建并配置 Flask 应用（应用工厂模式）"""
    app = Flask(__name__)

    # 加载配置文件
    app.config.from_object('config.Config')

    # Session 配置 - 会话保持
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)   # "记住我"有效期7天
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8) # 普通会话8小时

    # 将扩展绑定到 app 实例
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    bootstrap.init_app(app)

    # 登录管理器配置
    login_manager.login_view = 'auth.login'            # 未登录时重定向
    login_manager.login_message = '请先登录后再进行此操作'
    login_manager.login_message_category = 'warning'

    # 注册蓝图（各功能模块的路由）
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.booking import booking_bp
    from app.routes.credit_manage import cr_bp
    from app.routes.frontdesk import fd_bp
    from app.routes.hotel import room_bp
    from app.routes.main import main_bp
    from app.routes.query import qy_bp
    from app.routes.review import rv_bp

    app.register_blueprint(main_bp)                         # 首页/控制台
    app.register_blueprint(auth_bp, url_prefix='/auth')     # 认证
    app.register_blueprint(room_bp, url_prefix='/rooms')    # 客房管理+房型
    app.register_blueprint(booking_bp, url_prefix='/bookings')  # 预订/订单
    app.register_blueprint(admin_bp, url_prefix='/admin')   # 后台管理
    app.register_blueprint(fd_bp, url_prefix='/frontdesk')  # 前台业务
    app.register_blueprint(cr_bp, url_prefix='/credits')    # 挂账管理
    app.register_blueprint(qy_bp, url_prefix='/query')      # 查询统计+导出
    app.register_blueprint(rv_bp, url_prefix='/reviews')    # 客房评价

    # 导入模型，确保迁移脚本能发现所有模型
    from app import models  # noqa: F401

    # SQLite 自动建表 + 初始化管理员账号
    with app.app_context():
        db.create_all()
        _seed_admin()

    # 注入权限检查函数到模板全局上下文
    @app.context_processor
    def inject_permissions():
        return {
            'has_perm': lambda p: (
                current_user.is_authenticated and
                current_user.has_permission(p)
            )
        }

    return app
