#!/usr/bin/env bash
set -e

MODE=$1  # 参数: server 或 client
VENV_DIR=".venv"

# 创建并激活虚拟环境，避免系统托管环境限制
function setup_venv() {
  if [ ! -d "$VENV_DIR" ]; then
    echo "== 创建 Python 虚拟环境 (.venv) =="
    python3 -m venv "$VENV_DIR"
  fi
  echo "== 激活虚拟环境 =="
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
}

if [[ "$MODE" == "server" ]]; then
  echo "== 在 Server VM (192.168.228.141) 上启动 =="
  setup_venv
  echo "== 安装依赖 =="
  pip install --upgrade pip
  pip install -r requirements.txt
  echo "== 生成密钥与参数 =="
  python3 keygen.py
  echo "== 构建索引 =="
  python3 index_build.py
  echo "== 启动搜索服务器 =="
  python3 search_server.py
elif [[ "$MODE" == "client" ]]; then
  echo "== 在 Client VM (192.168.228.130) 上运行客户端 =="
  setup_venv
  echo "== 安装依赖 =="
  pip install --upgrade pip
  pip install -r requirements.txt
  echo "== 执行查询 =="
  python3 demo_client.py --query "encryption" --d 1 --k 5
else
  echo "用法: $0 server   # 启动 Server"
  echo "      $0 client   # 启动 Client"
fi