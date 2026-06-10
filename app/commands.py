"""Flask CLI 命令 - 数据库迁移与初始化"""
import json

import click


def register_commands(app):
    """注册自定义 CLI 命令"""

    @app.cli.command('seed')
    def seed():
        """初始化管理员账号（首次部署时执行，已存在则跳过）"""
        from app import db
        from app.models import Role, User

        if User.query.first() is not None:
            click.echo('⏭️  数据库已有用户，跳过初始化')
            return

        all_perms = [
            'user:manage', 'role:manage', 'room:view', 'room:manage',
            'room_type:manage', 'order:view', 'order:create', 'order:cancel',
            'order:checkin', 'order:checkout', 'credit:view', 'credit:manage',
            'stats:view', 'review:view', 'review:manage',
        ]
        admin_role = Role(role_name='管理员', permissions=json.dumps(all_perms))
        db.session.add(admin_role)
        db.session.flush()

        admin = User(username='admin', name='管理员', role_id=admin_role.id)
        admin.password = 'admin123'
        db.session.add(admin)
        db.session.commit()
        click.echo('✅ 已创建默认管理员: admin / admin123')
