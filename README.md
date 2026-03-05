# LogoLights

基于 ESP32-C3 SuperMini 的智能灯光控制系统，使用 MicroPython 开发。

## 功能特性

- **上升沿触发**：检测控制信号从低电平到高电平的跳变
- **进度条效果**：灯珠逐个点亮，营造流动效果
- **呼吸灯效果**：亮度平滑变化（亮→暗→亮→暗）
- **低功耗待机**：灯效完成后自动关闭灯光电源

## 硬件要求

| 组件 | 型号/规格 |
|------|-----------|
| 开发板 | ESP32-C3 SuperMini |
| 灯带 | WS2812B (21颗灯珠) |
| 雷达模块 | LD2410C |
| MOSFET | AO3401 (PMOS) |

## 引脚配置

| 功能 | GPIO | 说明 |
|------|------|------|
| RADAR_PIN | 2 | LD2410C OUT 引脚 |
| MOSFET_PIN | 4 | AO3401 栅极 (Gate) |
| LED_PIN | 5 | WS2812B 数据引脚 (DIN) |

## 灯效流程

```
上升沿触发 → 进度条效果 → 呼吸效果 → 关闭灯光 → 等待下一次触发
```

1. **进度条效果**：每个灯珠间隔 10ms 逐个点亮（暖白色）
2. **呼吸效果**：亮→暗→亮→暗，共3个周期

## 快速开始

### 1. 烧录 MicroPython 固件

```bash
# 擦除 flash
esptool --chip esp32c3 --port /dev/cu.usbmodem1101 erase-flash

# 烧录固件
esptool --chip esp32c3 --port /dev/cu.usbmodem1101 --baud 460800 write-flash --flash-size=detect 0x0 ESP32_GENERIC_C3-20251209-v1.27.0.bin
```

### 2. 上传代码

```bash
# 使用 mpremote 上传
python3 -m mpremote connect /dev/cu.usbmodem1101 cp main.py :main.py

# 软重启
python3 -m mpremote connect /dev/cu.usbmodem1101 soft-reset
```

### 3. 连接 REPL（可选）

```bash
screen /dev/cu.usbmodem1101 115200
# 或
python3 -m mpremote connect /dev/cu.usbmodem1101
```

## 配置修改

在 `main.py` 中可调整以下参数：

```python
LED_COUNT = 21      # 灯珠数量
time.sleep_ms(10)   # 进度条速度（progress_bar_effect）
time.sleep_ms(10)   # 呼吸速度（breathing_once）
```

## 电路说明

- **PMOS 控制**：AO3401 为 PMOS，低电平导通，高电平断开
- **电源管理**：灯效结束后切断灯带电源，降低功耗

## 项目结构

```
LogoLights/
├── main.py                              # 主程序
├── ESP32_GENERIC_C3-20251209-v1.27.0.bin # MicroPython 固件
└── README.md                            # 项目说明
```

## License

MIT
