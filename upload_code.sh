#!/bin/bash
# 上传程序到 ESP32-C3 (MicroPython)

set -e

# --- 配置 ---
PORT="${PORT:-/dev/cu.usbmodem1101}"
MPREMOTE="python3 -m mpremote"

# --- 颜色输出 ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== 程序上传工具 ===${NC}"
echo ""

# 检查端口
if [ ! -e "$PORT" ]; then
    echo -e "${YELLOW}警告: 端口 $PORT 不存在${NC}"
    echo "可用端口:"
    ls /dev/cu.usb* 2>/dev/null || echo "  (无)"
    echo ""
    echo "使用方法: PORT=/dev/cu.usbmodemXXXX $0"
    exit 1
fi

echo -e "端口: ${YELLOW}$PORT${NC}"
echo ""

# 上传配置文件
if [ -f "config.py" ]; then
    echo -e "${YELLOW}[1/2] 上传 config.py...${NC}"
    $MPREMOTE connect "$PORT" cp config.py :config.py
else
    echo -e "${YELLOW}[1/2] config.py 不存在，跳过${NC}"
fi

# 上传主程序
echo -e "${YELLOW}[2/2] 上传 main.py...${NC}"
$MPREMOTE connect "$PORT" cp main.py :main.py

# 软重启
echo ""
echo -e "${YELLOW}重启设备...${NC}"
$MPREMOTE connect "$PORT" soft-reset

echo ""
echo -e "${GREEN}上传完成！${NC}"
echo -e "${YELLOW}连接 REPL...${NC}"
echo ""
exec $MPREMOTE connect "$PORT"
