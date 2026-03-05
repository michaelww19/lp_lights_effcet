#!/bin/bash
# 烧录 MicroPython 固件到 ESP32-C3

set -e

# --- 配置 ---
CHIP="esp32c3"
PORT="${PORT:-/dev/cu.usbmodem1101}"
BAUD="460800"
FIRMWARE="ESP32_GENERIC_C3-20251209-v1.27.0.bin"

# --- 颜色输出 ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== ESP32-C3 固件烧录工具 ===${NC}"
echo ""

# 检查固件文件
if [ ! -f "$FIRMWARE" ]; then
    echo -e "${RED}错误: 找不到固件文件 $FIRMWARE${NC}"
    echo "请下载 MicroPython 固件到当前目录"
    exit 1
fi

# 检查端口
if [ ! -e "$PORT" ]; then
    echo -e "${YELLOW}警告: 端口 $PORT 不存在${NC}"
    echo "可用端口:"
    ls /dev/cu.usb* 2>/dev/null || echo "  (无)"
    echo ""
    echo "使用方法: PORT=/dev/cu.usbmodemXXXX $0"
    exit 1
fi

echo -e "芯片: ${YELLOW}$CHIP${NC}"
echo -e "端口: ${YELLOW}$PORT${NC}"
echo -e "固件: ${YELLOW}$FIRMWARE${NC}"
echo ""

# 擦除 flash
echo -e "${YELLOW}[1/2] 擦除 Flash...${NC}"
esptool --chip $CHIP --port "$PORT" erase-flash

# 烧录固件
echo ""
echo -e "${YELLOW}[2/2] 烧录固件...${NC}"
esptool --chip $CHIP --port "$PORT" --baud $BAUD write-flash --flash-size=detect 0x0 "$FIRMWARE"

echo ""
echo -e "${GREEN}固件烧录完成！${NC}"
echo "接下来运行 ./upload_code.sh 上传程序"
