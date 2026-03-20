#!/bin/bash
# RedOps Agent - 环境安装脚本 (Kali Linux 2024.4+ 兼容)
# 使用方法: bash setup_env.sh

set -e

echo "======================================"
echo "RedOps Agent - 环境安装"
echo "======================================"

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "[*] Python版本: $PYTHON_VERSION"

# 检查是否已有虚拟环境
if [ -d "venv" ]; then
    echo "[*] 检测到已有虚拟环境: venv"
    read -p "是否重新创建? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "[*] 删除旧环境..."
        rm -rf venv
    else
        echo "[*] 使用现有虚拟环境"
    fi
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "[*] 创建虚拟环境..."
    python3 -m venv venv
    echo "[+] 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "[*] 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "[*] 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "[*] 安装依赖包..."
pip install -r requirements.txt

echo ""
echo "======================================"
echo "[+] 环境安装完成!"
echo "======================================"
echo ""
echo "启动服务器:"
echo "  source venv/bin/activate"
echo "  python start_server.py"
echo ""
echo "或一键启动:"
echo "  ./start.sh"
