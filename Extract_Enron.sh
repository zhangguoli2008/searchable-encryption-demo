#!/usr/bin/env bash
set -e

# ----------------------------------------------------------------------------
# extract_enron.sh
# 从 Enron 邮件原始目录中抽取正文到 data/docs，每封邮件一个文件
# 使用方法:
#   放到项目根目录，下方示例假设在项目根运行：
#     bash extract_enron.sh
# ----------------------------------------------------------------------------

# 1. 定义路径
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$BASE_DIR/data"
RAW_DIR="$DATA_DIR/raw/enron_mail_20110402"
DST_DIR="$DATA_DIR/docs"

# 2. 确保目标目录存在
mkdir -p "$DST_DIR"

echo "[+] Extracting email bodies from $RAW_DIR into $DST_DIR..."

# 3. 遍历所有 .txt 文件并抽正文
find "$RAW_DIR" -type f -name '*.txt' | while IFS= read -r f; do
  # 去掉 RAW_DIR 前缀，生成唯一 ID，把中间斜杠替换为下划线
  id="${f#$RAW_DIR/}"
  id="${id//\//_}"

  # awk: 跳过头部直到遇见空行，再输出正文到目标文件
  awk '/^$/{flag=1; next} flag' "$f" > "$DST_DIR/${id}"

  # 打印进度
  echo "--> Wrote $DST_DIR/${id}"
done

# 4. 完成并输出统计
count=$(ls -1 "$DST_DIR" | wc -l)
echo "[+] Done. Total extracted files: $count"
