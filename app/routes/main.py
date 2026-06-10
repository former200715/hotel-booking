"""
首页/控制台路由
"""
from datetime import datetime

from flask import Blueprint, render_template
from flask_login import login_required

from app import db
from app.models import Credit, OrderRecord, Role, Room, RoomType, User

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    """首页控制台 - 数据概览 + 快捷入口"""
    stats = {
        'total_rooms': Room.query.count(),
        'available_rooms': Room.query.filter_by(status=Room.STATUS_AVAILABLE).count(),
        'occupied_rooms': Room.query.filter_by(status=Room.STATUS_OCCUPIED).count(),
        'total_orders': OrderRecord.query.count(),
        'confirmed_orders': OrderRecord.query.filter_by(order_status=OrderRecord.ORDER_CONFIRMED).count(),
        'completed_orders': OrderRecord.query.filter_by(order_status=OrderRecord.ORDER_COMPLETED).count(),
        'today_orders': OrderRecord.query.filter(
            OrderRecord.create_time >= datetime.now().replace(hour=0, minute=0, second=0)
        ).count(),
        'total_revenue': db.session.query(
            db.func.sum(OrderRecord.total_fee)
        ).filter(OrderRecord.order_status.in_([OrderRecord.ORDER_CONFIRMED, OrderRecord.ORDER_COMPLETED])).scalar() or 0,
        'total_users': User.query.count(),
        'total_roles': Role.query.count(),
        'unpaid_credits': Credit.query.filter(
            Credit.pay_status.in_([Credit.PAY_UNPAID, Credit.PAY_PARTIAL])
        ).count(),
    }

    # 最近订单
    recent_orders = (OrderRecord.query
                     .order_by(OrderRecord.create_time.desc())
                     .limit(8).all())

    # 房型分布
    types = RoomType.query.all()

    return render_template('index.html',
                           stats=stats,
                           recent_orders=recent_orders,
                           types=types)
