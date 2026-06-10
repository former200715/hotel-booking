"""
前台业务路由：入住登记、续费、退房结账、宿费提醒
"""
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import CheckinForm, CheckoutForm, RenewalForm
from app.models import Credit, OrderRecord, Room

fd_bp = Blueprint('frontdesk', __name__)


# ==================== 入住登记 ====================
@fd_bp.route('/checkin', methods=['GET', 'POST'])
@login_required
def checkin():
    """住宿登记"""
    form = CheckinForm()
    if form.validate_on_submit():
        room = db.session.get(Room, form.room_id.data)
        if not room or not room.is_available():
            flash('该房间不可用，请重新选择', 'danger')
            return redirect(url_for('frontdesk.checkin'))

        # 创建入住记录
        check_in_dt = datetime.now()
        check_out_dt = datetime.combine(form.check_out.data, datetime.min.time()) if form.check_out.data else None
        days = max((check_out_dt - check_in_dt).days, 1) if check_out_dt else 1
        total_fee = room.price * Decimal(str(days))

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
        room.status = Room.STATUS_OCCUPIED

        db.session.add(order)
        db.session.commit()

        flash(f'入住登记成功！{room.room_num} · {order.customer_name} · '
              f'预计费用 ¥{order.total_fee:.0f}', 'success')
        return redirect(url_for('booking.booking_list'))

    # GET 请求：展示登记页
    return render_template('frontdesk/checkin.html', form=form)


# ==================== 续费 ====================
@fd_bp.route('/renewal/<int:order_id>', methods=['GET', 'POST'])
@login_required
def renewal(order_id):
    """入住续费（延长退房时间）"""
    order = db.session.get(OrderRecord, order_id)
    if not order or order.order_status != OrderRecord.ORDER_CONFIRMED:
        flash('订单不存在或不可续费', 'danger')
        return redirect(url_for('booking.booking_list'))

    form = RenewalForm()
    if request.method == 'POST' and form.validate_on_submit():
        extend_days = form.extend_days.data
        old_checkout = order.check_out
        order.renew(extend_days)
        db.session.commit()

        flash(f'续费成功！退房时间：{old_checkout.strftime("%m-%d %H:%M")} → '
              f'{order.check_out.strftime("%m-%d %H:%M")}，'
              f'更新后总费用 ¥{order.total_fee:.0f}', 'success')
        return redirect(url_for('booking.booking_list'))

    return render_template('frontdesk/renewal.html', order=order, form=form)


# ==================== 结账 ====================
@fd_bp.route('/checkout/<int:order_id>', methods=['GET', 'POST'])
@login_required
def checkout(order_id):
    """退宿结算"""
    order = db.session.get(OrderRecord, order_id)
    if not order:
        flash('订单不存在', 'danger')
        return redirect(url_for('booking.booking_list'))
    if order.order_status not in [OrderRecord.ORDER_CONFIRMED]:
        flash('该订单状态不可结账', 'warning')
        return redirect(url_for('booking.booking_list'))

    form = CheckoutForm()
    if request.method == 'POST' and form.validate_on_submit():
        # 计算实际费用
        actual_checkout = form.actual_checkout.data or datetime.now()
        order.check_out = actual_checkout
        order.calculate_fee()

        # 应用折扣
        discount = form.discount.data or 0
        if discount > 0:
            order.total_fee = max(Decimal('0'), order.total_fee - discount)

        # 完成结账
        order.order_status = OrderRecord.ORDER_COMPLETED
        order.room.status = Room.STATUS_AVAILABLE

        # 如果选择挂账方式，创建挂账记录
        if form.payment_method.data == 'credit':
            credit = Credit(
                company_name=request.form.get('credit_company', '未指定单位'),
                order_id=order.id,
                debt_fee=order.total_fee
            )
            db.session.add(credit)

        db.session.commit()

        flash(f'结账完成！订单 #{order.id} · {order.customer_name} · '
              f'实付 ¥{order.total_fee:.0f} ({form.payment_method.data})', 'success')
        return redirect(url_for('booking.booking_list'))

    return render_template('frontdesk/checkout.html', order=order, form=form)


# ==================== 宿费提醒 ====================
@fd_bp.route('/reminders')
@login_required
def reminders():
    """超时未退房/费用提醒列表"""
    now = datetime.now()
    overdue_orders = OrderRecord.query.filter(
        OrderRecord.order_status == OrderRecord.ORDER_CONFIRMED,
        OrderRecord.check_out < now
    ).order_by(OrderRecord.check_out).all()

    # 近3天即将到期的订单
    upcoming_orders = OrderRecord.query.filter(
        OrderRecord.order_status == OrderRecord.ORDER_CONFIRMED,
        OrderRecord.check_out >= now,
        OrderRecord.check_out <= now + timedelta(days=3)
    ).order_by(OrderRecord.check_out).all()

    return render_template('frontdesk/reminders.html',
                           overdue_orders=overdue_orders,
                           upcoming_orders=upcoming_orders,
                           now=datetime.now())


@fd_bp.route('/reminders/<int:order_id>/mark', methods=['POST'])
@login_required
def mark_reminded(order_id):
    """标记已提醒"""
    order = db.session.get(OrderRecord, order_id)
    if order:
        order.reminded = True
        db.session.commit()
        flash(f'订单 #{order.id} 已标记为"已提醒"', 'success')
    return redirect(url_for('frontdesk.reminders'))
