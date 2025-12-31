#!/bin/bash

# WriteLoop 部署脚本
# 用于将前端构建并部署到 Nginx

set -e  # 遇到错误立即退出

echo "========================================="
echo "WriteLoop 部署脚本"
echo "========================================="

# 1. 前端构建
echo ""
echo "步骤 1: 构建前端..."
cd /root/WriteLoop

if [ ! -f "package.json" ]; then
    echo "错误: 找不到 package.json，请确认前端项目路径正确"
    exit 1
fi

echo "安装依赖..."
npm install

echo "构建项目..."
npm run build

if [ ! -d "dist" ]; then
    echo "错误: 构建失败，未找到 dist 目录"
    exit 1
fi

echo "前端构建完成！"
echo ""

# 2. 创建部署目录并复制文件
echo "步骤 2: 部署静态文件..."
DEPLOY_DIR="/var/www/writeloop"

# 创建目录（如果不存在）
sudo mkdir -p $DEPLOY_DIR

# 备份旧文件（如果存在）
if [ -d "$DEPLOY_DIR" ] && [ "$(ls -A $DEPLOY_DIR)" ]; then
    echo "备份旧文件到 ${DEPLOY_DIR}.backup..."
    sudo rm -rf ${DEPLOY_DIR}.backup
    sudo mv $DEPLOY_DIR ${DEPLOY_DIR}.backup
    sudo mkdir -p $DEPLOY_DIR
fi

# 复制新文件
echo "复制构建产物到 $DEPLOY_DIR..."
sudo cp -r /root/WriteLoop/dist/* $DEPLOY_DIR/

# 设置权限
sudo chown -R www-data:www-data $DEPLOY_DIR
sudo chmod -R 755 $DEPLOY_DIR

echo "文件部署完成！"
echo ""

# 3. Nginx 配置提示
echo "步骤 3: Nginx 配置"
echo "----------------------------------------"
echo "Nginx 配置文件已创建在: /root/writeloop-nginx.conf"
echo ""
echo "请执行以下命令来配置 Nginx:"
echo ""
echo "1. 复制配置文件到 Nginx 配置目录:"
echo "   sudo cp /root/writeloop-nginx.conf /etc/nginx/sites-available/writeloop"
echo ""
echo "2. 创建符号链接启用站点:"
echo "   sudo ln -s /etc/nginx/sites-available/writeloop /etc/nginx/sites-enabled/"
echo ""
echo "3. 测试 Nginx 配置:"
echo "   sudo nginx -t"
echo ""
echo "4. 如果测试通过，重新加载 Nginx:"
echo "   sudo systemctl reload nginx"
echo ""
echo "5. 确保后端服务正在运行（端口 8000）:"
echo "   cd /root/WriteLoopBackend"
echo "   uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "========================================="
echo "部署完成！"
echo "========================================="

