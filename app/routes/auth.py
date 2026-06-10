"""
认证路由：登录、注册、登出
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.forms import LoginForm, RegisterForm
from app.models import Role, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """操作员登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码错误', 'danger')
            return render_template('auth/login.html', form=form)

        if user.status == User.STATUS_DISABLED:
            flash('该账号已被禁用，请联系管理员', 'danger')
            return render_template('auth/login.html', form=form)

        login_user(user, remember=form.remember.data)
        flash(f'欢迎回来，{user.name}！', 'success')

        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.index'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """操作员注册"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        # 新注册操作员默认分配一个角色（若无角色则创建默认"前台"角色）
        default_role = Role.query.filter_by(role_name='前台').first()
        if not default_role:
            default_role = Role(
                role_name='前台',
                permissions='["room:view","order:create","order:view","order:cancel"]'
            )
            db.session.add(default_role)
            db.session.flush()

        user = User(
            username=form.username.data,
            name=form.name.data,
            role_id=default_role.id
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('注册成功，请登录！', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """操作员登出"""
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('auth.login'))
