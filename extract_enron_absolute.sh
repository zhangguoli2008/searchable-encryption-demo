#!/usr/bin/env bash
set -e

# ----------------------------------------------------------------------------
# extract_enron_absolute.sh
# 从 Enron 原始邮件目录中抽取正文到指定 docs 目录
# 支持 CRLF 换行兼容
#
# 使用方法：
#   1. 将本脚本保存为 extract_enron_absolute.sh 并放任意位置
#   2. 赋执行权限：chmod +x extract_enron_absolute.sh
#   3. 直接运行：./extract_enron_absolute.sh
#----------------------------------------------------------------------------

# 配置：
RAW_DIR="/home/zhangguoli/Document/searchable-encryption-demo/data/raw/enron_mail_20110402/maildir"
DST_DIR="/home/zhangguoli/Document/searchable-encryption-demo/data/docs"

# 确保目标目录存在
mkdir -p "$DST_DIR"

echo "[+] Extracting email bodies from: $RAW_DIR"
echo "[+] Output directory: $DST_DIR"

# 遍历并抽取
find "$RAW_DIR" -type f -name '*.txt' | while IFS= read -r f; do
  # 构造唯一文件名：去掉前缀，替换斜杠为下划线
  id="${f#$RAW_DIR/}"
  id="${id//\//_}"

  # sed删除CR，删除头部直到空行，剩下正文写入目标文件
  sed -e 's/\r$//' -e '1,/^$/d' "$f" > "$DST_DIR/$id"

  # 进度提示（可注释）
  echo "--> Wrote $DST_DIR/$id"
done

# 完成统计
total=$(ls "$DST_DIR" | wc -l)
echo "[+] Done. Total extracted files: $total"
