import os
import secrets

# 获取当前文件所在目录的绝对路径
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Flask 基础配置类"""

    # 安全密钥 - 从环境变量读取，开发环境自动生成随机密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # 数据库连接配置 - 优先使用 DATABASE_URL，否则回退到 SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        f'sqlite:///{os.path.join(BASE_DIR, "hotel_booking.db")}'
    )
    # 关闭追踪修改信号，节省内存
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 调试模式
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'

    # 分页配置
    HOTELS_PER_PAGE = 9
    PER_PAGE = int(os.environ.get('PER_PAGE', '15'))
