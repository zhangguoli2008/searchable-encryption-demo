#!/usr/bin/env bash
set -e
ROLE=$1

if [[ "$ROLE" == "server" ]]; then
  echo "== 安装依赖 =="
  pip3 install -r requirements.txt
  echo "== 生成密钥与参数 =="
  python3 keygen.py
  echo "== 构建索引 =="
  python3 index_build.py
  echo "== 启动搜索服务器 =="
  python3 search_server.py
elif [[ "$ROLE" == "client" ]]; then
  echo "== 安装依赖 =="
  pip3 install -r requirements.txt
  echo "请确保已从 server 机复制 server/params.json 到本地 server/params.json"
  read -p "请输入搜索服务器地址 (e.g. http://IP:5000): " SVR
  python3 demo_client.py --server $SVR --query "encryption" --d 1 --k 5
else
  echo "用法: $0 [server|client]"
fi