"""
酒店预订系统 - 数据模型模块 (7张表)
  user / role / room_type / room / order_record / credit / review
"""
from datetime import datetime
from decimal import Decimal

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


# ==================== 1. 角色表 ====================
class Role(db.Model):
    """角色表 - 定义操作员角色及权限"""
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='角色ID')
    role_name = db.Column(db.String(32), unique=True, nullable=False, comment='角色名称')
    permissions = db.Column(db.Text, nullable=True, comment='权限列表（JSON格式存储）')

    # 关联：一个角色下有多个操作员
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.role_name}>'


# ==================== 2. 操作员表 ====================
class User(UserMixin, db.Model):
    """操作员表 - 系统登录用户"""
    __tablename__ = 'user'

    # 状态常量
    STATUS_ENABLED = 'enabled'
    STATUS_DISABLED = 'disabled'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='操作员ID')
    username = db.Column(db.String(64), unique=True, nullable=False, comment='登录用户名')
    password_hash = db.Column('password', db.String(256), nullable=False, comment='密码（哈希存储）')
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False, comment='所属角色ID')
    name = db.Column(db.String(32), nullable=False, comment='真实姓名')
    status = db.Column(db.String(16), default=STATUS_ENABLED, comment='状态: enabled-启用, disabled-禁用')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    # 关联：一个操作员可处理多条预订记录
    order_records = db.relationship('OrderRecord', backref='operator', lazy='dynamic')

    def set_password(self, password):
        """设置密码 - 自动生成哈希值存入 password_hash 字段"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """校验密码 - 将明文与哈希值比对"""
        return check_password_hash(self.password_hash, password)

    @property
    def password(self):
        """禁止直接读取密码哈希"""
        raise AttributeError('密码不可直接读取')

    @password.setter
    def password(self, plain_text):
        """通过赋值语法设置密码: user.password = 'xxx'"""
        self.set_password(plain_text)

    def is_active(self):
        """Flask-Login 回调：判断账号是否可用"""
        return self.status == self.STATUS_ENABLED

    def get_permissions(self):
        """获取当前角色的权限列表"""
        import json
        if self.role and self.role.permissions:
            try:
                return json.loads(self.role.permissions)
            except json.JSONDecodeError:
                return []
        return []

    def has_permission(self, permission):
        """检查是否拥有指定权限"""
        return permission in self.get_permissions()

    def is_admin(self):
        """检查是否为管理员角色"""
        return self.role.role_name == '管理员' if self.role else False

    def __repr__(self):
        return f'<User {self.username} - {self.name}>'


# Flask-Login 用户加载器
@login_manager.user_loader
def load_user(user_id):
    """根据操作员ID加载用户对象（Flask-Login 要求）"""
    return db.session.get(User, int(user_id))


# ==================== 3. 客房类型表 ====================
class RoomType(db.Model):
    """客房类型表 - 定义房间类别（如标准间、大床房、套房等）"""
    __tablename__ = 'room_type'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='类型ID')
    type_name = db.Column(db.String(32), unique=True, nullable=False, comment='类型名称')
    base_price = db.Column(db.Numeric(10, 2), nullable=False, comment='基础价格（元/晚）')
    facility = db.Column(db.String(256), nullable=True, comment='配套设施（逗号分隔）')

    # 关联：一个类型下有多间具体客房
    rooms = db.relationship('Room', backref='room_type', lazy='dynamic')

    def __repr__(self):
        return f'<RoomType {self.type_name}>'


# ==================== 4. 客房表 ====================
class Room(db.Model):
    """客房表 - 具体的房间，每间房有唯一房号"""
    __tablename__ = 'room'

    # 房间状态常量
    STATUS_AVAILABLE = 'available'    # 空闲
    STATUS_OCCUPIED = 'occupied'      # 已入住
    STATUS_RESERVED = 'reserved'      # 已预订
    STATUS_MAINTENANCE = 'maintenance' # 维护中

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='客房ID')
    room_num = db.Column(db.String(16), unique=True, nullable=False, comment='房间号')
    type_id = db.Column(db.Integer, db.ForeignKey('room_type.id'), nullable=False, comment='所属房型ID')
    floor = db.Column(db.SmallInteger, nullable=False, comment='所在楼层')
    price = db.Column(db.Numeric(10, 2), nullable=False, comment='实际售价（元/晚）')
    status = db.Column(db.String(16), default=STATUS_AVAILABLE,
                       comment='状态: available-空闲, occupied-已入住, reserved-已预订, maintenance-维护中')
    remark = db.Column(db.String(256), nullable=True, comment='备注信息')

    # 关联：一间客房可能有多条入住记录
    order_records = db.relationship('OrderRecord', backref='room', lazy='dynamic')

    def is_available(self):
        """检查房间当前是否空闲可订"""
        return self.status == self.STATUS_AVAILABLE

    def __repr__(self):
        return f'<Room {self.room_num} - {self.room_type.type_name if self.room_type else "未知"}>'


# ==================== 5. 入住预订表 ====================
class OrderRecord(db.Model):
    """入住预订表 - 记录每一次入住/预订信息"""
    __tablename__ = 'order_record'

    # 订单状态常量
    ORDER_PENDING = 'pending'       # 待确认
    ORDER_CONFIRMED = 'confirmed'   # 已确认/已入住
    ORDER_COMPLETED = 'completed'   # 已完成/已退房
    ORDER_CANCELLED = 'cancelled'   # 已取消

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='订单ID')
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True,
                            comment='操作员ID（可为空，表示顾客自助预订）')
    customer_name = db.Column(db.String(32), nullable=False, comment='客户姓名')
    phone = db.Column(db.String(20), nullable=False, comment='联系电话')
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False, comment='入住房间ID')
    check_in = db.Column(db.DateTime, nullable=False, comment='入住时间')
    check_out = db.Column(db.DateTime, nullable=True, comment='退房时间（NULL表示未退房）')
    total_fee = db.Column(db.Numeric(10, 2), nullable=False, comment='总费用')
    renewal_count = db.Column(db.Integer, default=0, comment='续费次数')
    reminded = db.Column(db.Boolean, default=False, comment='是否已催款提醒')
    order_status = db.Column(db.String(16), default=ORDER_PENDING,
                             comment='订单状态: pending-待确认, confirmed-已确认, completed-已完成, cancelled-已取消')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    # 关联：一个订单可能对应一条挂账记录
    credit = db.relationship('Credit', backref='order_record', uselist=False,
                             cascade='all, delete-orphan')

    def calculate_fee(self, nights=None):
        """计算总费用 = 房间单价 × 入住天数（如果退房时间为NULL则使用指定天数）"""
        if self.room:
            if self.check_out:
                days = (self.check_out - self.check_in).days
                days = max(days, 1)
            elif nights:
                days = nights
            else:
                days = 1
            self.total_fee = self.room.price * Decimal(str(days))

    def cancel(self):
        """取消订单，将对应房间状态恢复为空闲"""
        if self.order_status != self.ORDER_CANCELLED:
            self.order_status = self.ORDER_CANCELLED
            if self.room and self.room.status == Room.STATUS_RESERVED:
                self.room.status = Room.STATUS_AVAILABLE

    def renew(self, extend_days):
        """续费：延长退房时间，增加续费次数"""
        from datetime import timedelta
        if self.check_out:
            self.check_out = self.check_out + timedelta(days=extend_days)
        else:
            self.check_out = datetime.now() + timedelta(days=extend_days)
        self.renewal_count += 1
        # 重新计算总费用
        self.calculate_fee()

    @property
    def is_overdue(self):
        """判断是否超时未退房（check_out已过且未退房）"""
        if self.check_out and self.order_status == self.ORDER_CONFIRMED:
            return datetime.now() > self.check_out
        return False

    @property
    def nights_stayed(self):
        """已住天数"""
        if self.check_in:
            end = self.check_out if self.check_out else datetime.now()
            return max((end - self.check_in).days, 1)
        return 0

    def __repr__(self):
        return f'<OrderRecord #{self.id} - {self.order_status}>'


# ==================== 6. 挂账表 ====================
class Credit(db.Model):
    """挂账表 - 记录企业客户的欠款/挂账信息"""
    __tablename__ = 'credit'

    # 还款状态常量
    PAY_UNPAID = 'unpaid'      # 未还款
    PAY_PARTIAL = 'partial'    # 部分还款
    PAY_FULL = 'full'          # 已还清

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='挂账ID')
    company_name = db.Column(db.String(128), nullable=False, comment='挂账公司名称')
    order_id = db.Column(db.Integer, db.ForeignKey('order_record.id'), unique=True,
                         nullable=False, comment='关联订单ID（一对一）')
    debt_fee = db.Column(db.Numeric(10, 2), nullable=False, comment='挂账金额')
    paid_amount = db.Column(db.Numeric(10, 2), default=0, comment='已还金额')
    pay_status = db.Column(db.String(16), default=PAY_UNPAID,
                           comment='还款状态: unpaid-未还, partial-部分, full-还清')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='挂账创建时间')

    @property
    def remaining_debt(self):
        """剩余欠款 = 挂账金额 - 已还金额"""
        return (self.debt_fee or 0) - (self.paid_amount or 0)

    def make_payment(self, amount):
        """还款操作，自动更新还款状态"""
        self.paid_amount = (self.paid_amount or 0) + amount
        remaining = float(self.remaining_debt)
        if remaining <= 0:
            self.pay_status = self.PAY_FULL
        elif float(self.paid_amount) > 0:
            self.pay_status = self.PAY_PARTIAL

    def __repr__(self):
        return f'<Credit {self.company_name} - ¥{self.debt_fee} - {self.pay_status}>'


# ==================== 7. 客房评价表 ====================
class Review(db.Model):
    """客房评价表"""
    __tablename__ = 'review'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='评价ID')
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False, comment='房间ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, comment='评价人ID')
    rating = db.Column(db.SmallInteger, nullable=False, comment='评分(1-5星)')
    content = db.Column(db.Text, nullable=True, comment='评价内容')
    tags = db.Column(db.String(256), nullable=True, comment='标签(逗号分隔)')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='评价时间')

    room = db.relationship('Room', backref=db.backref('reviews', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Review #{self.id} {self.rating}★ - Room {self.room_id}>'
