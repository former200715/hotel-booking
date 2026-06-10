"""
酒店预订系统启动入口
运行方式: python run.py
"""
import os
from app import create_app

# 创建 Flask 应用实例
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
