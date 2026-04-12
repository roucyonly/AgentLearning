#!/bin/bash

echo "================================"
echo "高校教师数字分身系统 - 启动脚本"
echo "================================"
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ .env 文件不存在,请先复制 .env.example 为 .env 并填入配置"
    exit 1
fi

echo "✅ .env 文件存在"

# 初始化数据库
echo ""
echo "📦 初始化数据库..."
python init_db.py

if [ $? -ne 0 ]; then
    echo "❌ 数据库初始化失败"
    exit 1
fi

echo "✅ 数据库初始化成功"

# 启动 FastAPI 服务
echo ""
echo "🚀 启动 FastAPI 服务..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000
