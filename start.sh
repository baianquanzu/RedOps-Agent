#!/bin/bash
# RedOps Agent - 一键启动脚本 (Kali Linux 2024.4+ 兼容)

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "[!] 虚拟环境不存在，正在创建..."
    bash setup_env.sh
fi

# 激活虚拟环境并启动
echo "[*] 激活虚拟环境..."
source venv/bin/activate

echo "[*] 启动 RedOps Agent 服务器..."
python start_server.py
