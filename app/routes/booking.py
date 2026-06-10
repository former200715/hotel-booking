"""
预订路由：创建预订、订单列表、取消预订、挂账管理
"""
from datetime import datetime
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import BookingForm
from app.models import OrderRecord, Room

booking_bp = Blueprint('booking', __name__)


@booking_bp.route('/')
@login_required
def booking_list():
    """订单列表：展示全部订单（倒序）"""
    orders = (OrderRecord.query
              .order_by(OrderRecord.create_time.desc())
              .all())
    return render_template('bookings/list.html', orders=orders)


@booking_bp.route('/create', methods=['POST'])
@login_required
def create_booking():
    """创建入住预订（处理 POST 请求）"""
    form = BookingForm()
    if form.validate_on_submit():
        room = db.session.get(Room, int(form.room_id.data))
        if not room:
            flash('房间信息无效', 'danger')
            return redirect(url_for('main.index'))

        # 检查房间状态
        if not room.is_available():
            flash('抱歉，该房间当前不可预订', 'danger')
            return redirect(url_for('room.room_detail', room_id=room.id))

        # 将 check_in/check_out date 转为 datetime
        check_in_dt = datetime.combine(form.check_in.data, datetime.min.time())
        check_out_dt = datetime.combine(form.check_out.data, datetime.min.time())
        days = max((check_out_dt - check_in_dt).days, 1)
        total_fee = room.price * Decimal(str(days))

        # 创建订单
        order = OrderRecord(
            operator_id=current_user.id,
            customer_name=form.customer_name.data,
            phone=form.phone.data,
            room_id=room.id,
            check_in=check_in_dt,
            check_out=check_out_dt,
            total_fee=total_fee,
            order_status=OrderRecord.ORDER_CONFIRMED
        )

        # 更新房间状态为已预订
        room.status = Room.STATUS_RESERVED

        db.session.add(order)
        db.session.commit()

        flash(f'预订成功！订单编号：{order.id}，总费用：¥{order.total_fee}', 'success')
        return redirect(url_for('booking.booking_list'))

    # 表单校验失败
    for _field, errors in form.errors.items():
        for error in errors:
            flash(f'{error}', 'danger')
    return redirect(request.referrer or url_for('main.index'))


@booking_bp.route('/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(order_id):
    """取消预订"""
    order = db.session.get(OrderRecord, order_id)

    if not order:
        flash('订单不存在', 'danger')
        return redirect(url_for('booking.booking_list'))

    if order.order_status == OrderRecord.ORDER_CANCELLED:
        flash('该订单已取消', 'info')
    elif order.order_status == OrderRecord.ORDER_COMPLETED:
        flash('已完成的订单不可取消', 'warning')
    else:
        order.cancel()
        db.session.commit()
        flash(f'订单 #{order.id} 已取消', 'success')

    return redirect(url_for('booking.booking_list'))


@booking_bp.route('/<int:order_id>/checkout', methods=['POST'])
@login_required
def checkout(order_id):
    """办理退房 - 重定向到完整结算流程"""
    return redirect(url_for('frontdesk.checkout', order_id=order_id))
