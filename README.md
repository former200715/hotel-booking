# 酒店预订管理系统

基于 Python Flask + MySQL + Bootstrap5 + ECharts 的酒店预订管理系统。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python Flask 3.x |
| ORM | Flask-SQLAlchemy |
| 认证 | Flask-Login (会话保持 + 权限拦截) |
| 数据库 | MySQL (pymysql) |
| 迁移 | Flask-Migrate |
| 前端 | Bootstrap 5.3 + Bootstrap Icons |
| 图表 | ECharts 5.5 |
| Excel导出 | openpyxl |
| 安全 | Werkzeug密码哈希 + CSRF保护 |

## 快速启动

### 1. 安装依赖
```bash
cd D:/Users/ABC/Desktop/酒店预订
pip install -r requirements.txt
```

### 2. 创建数据库
```sql
CREATE DATABASE hotel_booking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 配置数据库连接
编辑 `config.py`，修改 `MYSQL_USER` / `MYSQL_PASSWORD` 等参数。

### 4. 初始化表结构
```bash
flask db init
flask db migrate -m "init"
flask db upgrade
```

### 5. 创建初始管理员
```bash
flask shell
```
```python
from app import db
from app.models import Role, User

# 创建管理员角色
admin_role = Role(role_name='管理员', permissions='["admin:dashboard","room:view","room:manage","order:create","order:view","order:cancel","order:checkout","credit:view","credit:manage","user:manage","role:manage","system:settings"]')
db.session.add(admin_role)

# 创建管理员账号
admin = User(username='admin', name='系统管理员', role_id=1, status='enabled')
admin.set_password('admin123')
db.session.add(admin)
db.session.commit()
exit()
```

### 6. 启动
```bash
python run.py
# 浏览器打开 http://localhost:5000
# 管理员: admin / admin123
```

## 功能页面清单

| # | 页面 | URL | 功能说明 |
|---|------|-----|----------|
| 1 | 登录页 | `/auth/login` | 全屏登录，支持"记住我"7天免登录 |
| 2 | 注册页 | `/auth/register` | 操作员自助注册 |
| 3 | 控制台 | `/` | 统计卡片 + 房间概览 + 订单图表 + 最近订单 |
| 4 | 数据统计 | `/query/stats` | ECharts饼图/柱状图/趋势图 + 导出Excel |
| 5 | 订单查询 | `/query/bookings` | 多条件组合查询 + 分页 + 导出 |
| 6 | 挂账查询 | `/query/credits` | 挂账搜索 + 分页 + 导出 |
| 7 | 房态面板 | `/rooms/` | 房间卡片网格 + 颜色编码 + 多维度筛选 |
| 8 | 房型管理 | `/rooms/types` | 房型CRUD + 弹窗编辑 |
| 9 | 客房管理 | `/rooms/manage` | 房间CRUD + 批量管理 |
| 10 | 客房详情 | `/rooms/<id>` | 房间信息 + 入住历史 + 评价区 |
| 11 | 订单管理 | `/bookings/` | 订单列表 + 续费/结账/取消 |
| 12 | 住宿登记 | `/frontdesk/checkin` | 前台入住 + 房间分配 + 信息录入 |
| 13 | 入住续费 | `/frontdesk/renewal/<id>` | 延长退房 + 自动重算费用 |
| 14 | 退房结账 | `/frontdesk/checkout/<id>` | 费用明细 + 折扣 + 多支付方式 |
| 15 | 宿费提醒 | `/frontdesk/reminders` | 超时列表 + 3天预警 + 标记已提醒 |
| 16 | 挂账管理 | `/credits/` | 挂账CRUD + 还款 + 统计 |
| 17 | 操作员管理 | `/admin/users` | 增删改 + 角色分配 + 密码重置 |
| 18 | 角色权限 | `/admin/roles` | 12项权限复选框 + 角色CRUD |
| 19 | 系统设置 | `/admin/settings` | 系统参数 + 信息查看 |
| 20 | 客房评价 | `/reviews/<room_id>` | 评价列表 + 星级评分提交 |

## 7张数据表

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| role | 角色表 | role_name, permissions(JSON) |
| user | 操作员表 | username, password(哈希), role_id |
| room_type | 客房类型表 | type_name, base_price, facility |
| room | 客房表 | room_num, type_id, floor, price, status |
| order_record | 入住预订表 | customer_name, room_id, check_in/out, total_fee, order_status |
| credit | 挂账表 | company_name, order_id, debt_fee, paid_amount, pay_status |
| review | 评价表 | room_id, user_id, rating(1-5), content, tags |

## 项目结构

```
酒店预订/
├── run.py                    # 启动入口
├── config.py                 # 数据库+密钥配置
├── requirements.txt          # 8个依赖包
├── README.md                 # 本文档
└── app/
    ├── __init__.py           # 应用工厂 + 权限装饰器
    ├── models.py             # 7张数据表模型
    ├── forms.py              # 15个表单类
    ├── routes/
    │   ├── main.py           # 控制台首页
    │   ├── auth.py           # 认证 (登录/注册/登出)
    │   ├── hotel.py          # 客房+房型管理
    │   ├── booking.py        # 订单管理
    │   ├── admin.py          # 系统管理 (用户/角色/设置)
    │   ├── frontdesk.py      # 前台业务 (登记/续费/结账/提醒)
    │   ├── credit_manage.py  # 挂账管理
    │   ├── query.py          # 统计查询 + Excel导出
    │   └── review.py         # 客房评价
    ├── templates/            # 20个HTML模板
    │   ├── base.html         # 侧边栏母版
    │   ├── index.html        # 控制台仪表盘
    │   ├── auth/             # login + register
    │   ├── rooms/            # status + types + manage + detail
    │   ├── bookings/         # list
    │   ├── frontdesk/        # checkin + checkout + renewal + reminders
    │   ├── credit/           # list
    │   ├── admin/            # users + roles + settings
    │   ├── query/            # stats + bookings + credits
    │   └── review/           # list
    └── static/css/style.css  # 全局样式
```
