#!/bin/bash
# Railway 启动脚本: 先迁移数据库，再初始化数据，最后启动服务
set -e

echo "🔄 执行数据库迁移..."
flask db upgrade

echo "🌱 初始化管理员账号（如已存在则跳过）..."
flask seed

echo "🚀 启动 Web 服务..."
exec gunicorn "app:create_app()"
