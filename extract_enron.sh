#!/usr/bin/env bash
set -e

# 配置——请根据你的环境修改这两个路径：
RAW_DIR="/home/gl/Document/searchable-encryption-demo/data/raw/enron_mail_20110402/maildir"
DST_DIR="/home/gl/Document/searchable-encryption-demo/data/docs"

# 1. 确保目标目录存在
mkdir -p "$DST_DIR"

echo "[+] Extracting from $RAW_DIR to $DST_DIR …"

# 2. 遍历所有文件（排除 DELETIONS.txt）
find "$RAW_DIR" -type f ! -name 'DELETIONS.txt' | while IFS= read -r f; do
  # 2.1 构造文件 ID：去掉 RAW_DIR 前缀，再把 / 换成 _
  id="${f#$RAW_DIR/}"
  id="${id//\//_}"

  # 2.2 抽正文：跳过头部到第一个空行，再输出正文
  #     用 awk，更加通用（兼容 CRLF/LF）
  awk '/^\r?$/ {flag=1; next} flag' "$f" \
    > "$DST_DIR/${id}txt"

  # 进度提示（可注释掉以加速）
  echo "→ $DST_DIR/${id}.txt"
done

# 3. 完成汇总
echo "[+] Done. Total files written: $(ls "$DST_DIR" | wc -l)"

