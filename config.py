import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Flask 基础配置类"""
    # 安全密钥 - 从环境变量读取，开发环境自动生成随机密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # 数据库连接配置 修复逻辑：先判断环境变量是否存在，再处理协议
    raw_uri = os.environ.get("DATABASE_URL")
    if raw_uri and not raw_uri.startswith("${{"):
        # 线上Railway部署后变量会被解析为真实postgres链接
        if raw_uri.startswith("postgres://"):
            raw_uri = raw_uri.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = raw_uri
    else:
        # 本地开发/Console手动执行时回退SQLite
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "hotel_booking.db")}'

    # 关闭追踪修改信号，节省内存
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 调试模式
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'

    # 分页配置
    HOTELS_PER_PAGE = 9
    PER_PAGE = int(os.environ.get('PER_PAGE', '15'))