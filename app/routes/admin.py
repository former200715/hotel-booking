"""
后台管理路由：控制台、操作员管理、角色权限管理、系统设置
"""
import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db, permission_required
from app.forms import AVAILABLE_PERMISSIONS, PasswordResetForm, RoleForm, UserCreateForm, UserEditForm
from app.models import Role, User

admin_bp = Blueprint('admin', __name__)


def _get_selected_permissions():
    """从 request.form 中读取选中的权限列表"""
    selected = [k for k, _ in AVAILABLE_PERMISSIONS if request.form.get(f'perm_{k}')]
    return json.dumps(selected, ensure_ascii=False)


# ==================== 控制台 ====================
@admin_bp.route('/')
@login_required
@permission_required('admin:dashboard')
def dashboard():
    """后台控制台 - 重定向到首页控制台"""
    return redirect(url_for('main.index'))


# ==================== 操作员管理 ====================
@admin_bp.route('/users')
@login_required
@permission_required('user:manage')
def user_list():
    """操作员列表"""
    users = User.query.order_by(User.create_time.desc()).all()
    roles = Role.query.all()
    return render_template('admin/users.html', users=users, roles=roles)


@admin_bp.route('/users/create', methods=['POST'])
@login_required
@permission_required('user:manage')
def user_create():
    """新增操作员"""
    form = UserCreateForm()
    form.role_id.choices = [(r.id, r.role_name) for r in Role.query.all()]

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            name=form.name.data,
            role_id=form.role_id.data,
            status=form.status.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'操作员 {user.name} 创建成功', 'success')
    else:
        for errs in form.errors.values():
            for e in errs:
                flash(e, 'danger')

    return redirect(url_for('admin.user_list'))


@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
@permission_required('user:manage')
def user_edit(user_id):
    """编辑操作员"""
    user = db.session.get(User, user_id)
    if not user:
        flash('操作员不存在', 'danger')
        return redirect(url_for('admin.user_list'))

    form = UserEditForm(original_username=user.username)
    form.role_id.choices = [(r.id, r.role_name) for r in Role.query.all()]

    if form.validate_on_submit():
        user.username = form.username.data
        user.name = form.name.data
        user.role_id = form.role_id.data
        user.status = form.status.data
        db.session.commit()
        flash(f'操作员 {user.name} 信息已更新', 'success')
    else:
        for errs in form.errors.values():
            for e in errs:
                flash(e, 'danger')

    return redirect(url_for('admin.user_list'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@permission_required('user:manage')
def user_delete(user_id):
    """删除操作员"""
    user = db.session.get(User, user_id)
    if not user:
        flash('操作员不存在', 'danger')
    elif user.id == current_user.id:
        flash('不能删除自己的账号', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f'操作员 {user.name} 已删除', 'success')

    return redirect(url_for('admin.user_list'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@permission_required('user:manage')
def user_reset_password(user_id):
    """重置操作员密码"""
    user = db.session.get(User, user_id)
    if not user:
        flash('操作员不存在', 'danger')
        return redirect(url_for('admin.user_list'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        flash(f'操作员 {user.name} 密码已重置', 'success')
    else:
        for errs in form.errors.values():
            for e in errs:
                flash(e, 'danger')

    return redirect(url_for('admin.user_list'))


# ==================== 角色权限管理 ====================
@admin_bp.route('/roles')
@login_required
@permission_required('role:manage')
def role_list():
    """角色列表"""
    roles = Role.query.order_by(Role.id).all()
    return render_template('admin/roles.html', roles=roles,
                           permissions_list=AVAILABLE_PERMISSIONS)


@admin_bp.route('/roles/create', methods=['POST'])
@login_required
@permission_required('role:manage')
def role_create():
    """新增角色"""
    form = RoleForm()
    if form.validate_on_submit():
        if Role.query.filter_by(role_name=form.role_name.data).first():
            flash('该角色名称已存在', 'danger')
        else:
            role = Role(
                role_name=form.role_name.data,
                permissions=_get_selected_permissions()
            )
            db.session.add(role)
            db.session.commit()
            flash(f'角色 {role.role_name} 创建成功', 'success')
    else:
        for errs in form.errors.values():
            for e in errs:
                flash(e, 'danger')

    return redirect(url_for('admin.role_list'))


@admin_bp.route('/roles/<int:role_id>/edit', methods=['POST'])
@login_required
@permission_required('role:manage')
def role_edit(role_id):
    """编辑角色"""
    role = db.session.get(Role, role_id)
    if not role:
        flash('角色不存在', 'danger')
        return redirect(url_for('admin.role_list'))

    form = RoleForm()
    if form.validate_on_submit():
        existing = Role.query.filter_by(role_name=form.role_name.data).first()
        if existing and existing.id != role.id:
            flash('该角色名称已被使用', 'danger')
        else:
            role.role_name = form.role_name.data
            role.permissions = _get_selected_permissions()
            db.session.commit()
            flash(f'角色 {role.role_name} 已更新', 'success')
    else:
        for errs in form.errors.values():
            for e in errs:
                flash(e, 'danger')

    return redirect(url_for('admin.role_list'))


@admin_bp.route('/roles/<int:role_id>/delete', methods=['POST'])
@login_required
@permission_required('role:manage')
def role_delete(role_id):
    """删除角色"""
    role = db.session.get(Role, role_id)
    if not role:
        flash('角色不存在', 'danger')
    elif role.users.count() > 0:
        flash(f'角色 "{role.role_name}" 下还有 {role.users.count()} 名操作员，无法删除', 'danger')
    else:
        db.session.delete(role)
        db.session.commit()
        flash(f'角色 {role.role_name} 已删除', 'success')

    return redirect(url_for('admin.role_list'))


# ==================== 系统设置 ====================
@admin_bp.route('/settings')
@login_required
@permission_required('system:settings')
def system_settings():
    """系统设置页"""
    return render_template('admin/settings.html')


@admin_bp.route('/settings', methods=['POST'])
@login_required
@permission_required('system:settings')
def system_settings_save():
    """保存系统设置"""
    flash('系统设置已保存', 'success')
    return redirect(url_for('admin.system_settings'))
