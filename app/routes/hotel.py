"""
客房模块路由：房型管理、客房管理、房态面板
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.forms import RoomForm, RoomTypeForm
from app.models import Room, RoomType

room_bp = Blueprint('room', __name__)


# ==================== 房态面板 ====================
@room_bp.route('/')
@login_required
def list_rooms():
    """房态总览：卡片式展示所有房间状态"""
    type_id = request.args.get('type_id', type=int)
    status = request.args.get('status', '').strip()
    floor = request.args.get('floor', type=int)

    types = RoomType.query.all()
    floors = [r[0] for r in Room.query.with_entities(Room.floor).distinct().order_by(Room.floor).all()]

    query = Room.query
    if type_id: query = query.filter_by(type_id=type_id)
    if status:  query = query.filter_by(status=status)
    if floor:   query = query.filter_by(floor=floor)

    rooms = query.order_by(Room.floor, Room.room_num).all()

    # 统计数据
    stats = {
        'total': Room.query.count(),
        'available': Room.query.filter_by(status=Room.STATUS_AVAILABLE).count(),
        'occupied': Room.query.filter_by(status=Room.STATUS_OCCUPIED).count(),
        'reserved': Room.query.filter_by(status=Room.STATUS_RESERVED).count(),
        'maintenance': Room.query.filter_by(status=Room.STATUS_MAINTENANCE).count(),
    }

    return render_template('rooms/status.html', rooms=rooms, types=types,
                           floors=floors, stats=stats,
                           current_type=type_id, current_status=status,
                           current_floor=floor)


@room_bp.route('/<int:room_id>')
@login_required
def room_detail(room_id):
    """房间详情 + 入住历史"""
    room = db.session.get(Room, room_id)
    if not room: flash('房间不存在', 'danger'); return redirect(url_for('room.list_rooms'))

    from app.models import OrderRecord
    orders = (OrderRecord.query.filter_by(room_id=room_id)
              .order_by(OrderRecord.create_time.desc()).limit(10).all())

    return render_template('rooms/detail.html', room=room, orders=orders)


# ==================== 房型管理 ====================
@room_bp.route('/types')
@login_required
def type_list():
    """房型列表"""
    types = RoomType.query.order_by(RoomType.id).all()
    return render_template('rooms/types.html', types=types)


@room_bp.route('/types/create', methods=['POST'])
@login_required
def type_create():
    """新增房型"""
    form = RoomTypeForm()
    if form.validate_on_submit():
        rt = RoomType(type_name=form.type_name.data, base_price=form.base_price.data,
                      facility=form.facility.data)
        db.session.add(rt)
        db.session.commit()
        flash(f'房型「{rt.type_name}」已创建', 'success')
    else:
        for errs in form.errors.values():
            for e in errs: flash(e, 'danger')
    return redirect(url_for('room.type_list'))


@room_bp.route('/types/<int:type_id>/edit', methods=['POST'])
@login_required
def type_edit(type_id):
    """编辑房型"""
    rt = db.session.get(RoomType, type_id)
    if not rt: flash('房型不存在', 'danger'); return redirect(url_for('room.type_list'))

    form = RoomTypeForm(original_name=rt.type_name)
    if form.validate_on_submit():
        rt.type_name = form.type_name.data
        rt.base_price = form.base_price.data
        rt.facility = form.facility.data
        db.session.commit()
        flash(f'房型「{rt.type_name}」已更新', 'success')
    else:
        for errs in form.errors.values():
            for e in errs: flash(e, 'danger')
    return redirect(url_for('room.type_list'))


@room_bp.route('/types/<int:type_id>/delete', methods=['POST'])
@login_required
def type_delete(type_id):
    """删除房型"""
    rt = db.session.get(RoomType, type_id)
    if not rt: flash('房型不存在', 'danger')
    elif rt.rooms.count() > 0:
        flash(f'房型「{rt.type_name}」下有 {rt.rooms.count()} 间客房，请先移除客房', 'danger')
    else:
        db.session.delete(rt)
        db.session.commit()
        flash(f'房型「{rt.type_name}」已删除', 'success')
    return redirect(url_for('room.type_list'))


# ==================== 客房管理 ====================
@room_bp.route('/manage')
@login_required
def room_manage():
    """客房管理列表"""
    rooms = Room.query.order_by(Room.floor, Room.room_num).all()
    types = RoomType.query.all()
    return render_template('rooms/manage.html', rooms=rooms, types=types)


@room_bp.route('/manage/create', methods=['POST'])
@login_required
def room_create():
    """新增客房"""
    form = RoomForm()
    if form.validate_on_submit():
        room = Room(room_num=form.room_num.data, type_id=form.type_id.data,
                    floor=form.floor.data, price=form.price.data,
                    status=form.status.data, remark=form.remark.data)
        db.session.add(room)
        db.session.commit()
        flash(f'客房 {room.room_num} 已创建', 'success')
    else:
        for errs in form.errors.values():
            for e in errs: flash(e, 'danger')
    return redirect(url_for('room.room_manage'))


@room_bp.route('/manage/<int:room_id>/edit', methods=['POST'])
@login_required
def room_edit(room_id):
    """编辑客房"""
    room = db.session.get(Room, room_id)
    if not room: flash('客房不存在', 'danger'); return redirect(url_for('room.room_manage'))

    form = RoomForm(original_room_num=room.room_num, formdata=request.form)
    if form.validate_on_submit():
        room.room_num = form.room_num.data
        room.type_id = form.type_id.data
        room.floor = form.floor.data
        room.price = form.price.data
        room.status = form.status.data
        room.remark = form.remark.data
        db.session.commit()
        flash(f'客房 {room.room_num} 已更新', 'success')
    else:
        for errs in form.errors.values():
            for e in errs: flash(e, 'danger')
    return redirect(url_for('room.room_manage'))


@room_bp.route('/manage/<int:room_id>/delete', methods=['POST'])
@login_required
def room_delete(room_id):
    """删除客房"""
    room = db.session.get(Room, room_id)
    if not room: flash('客房不存在', 'danger')
    elif room.order_records.count() > 0:
        flash(f'客房 {room.room_num} 有入住记录，无法删除', 'danger')
    else:
        db.session.delete(room)
        db.session.commit()
        flash(f'客房 {room.room_num} 已删除', 'success')
    return redirect(url_for('room.room_manage'))
