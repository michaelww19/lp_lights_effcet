import machine
import neopixel
import time

# --- 加载配置 ---
try:
    from config import (
        RADAR_PIN, MOSFET_PIN, LED_PIN, LED_COUNT,
        COLOR_MODE, CUSTOM_COLOR,
        BREATHING_STEPS, PROGRESS_DELAY_MS, BREATHING_DELAY_MS
    )
except ImportError:
    # 默认配置（如果没有 config.py）
    RADAR_PIN = 2
    MOSFET_PIN = 4
    LED_PIN = 5
    LED_COUNT = 21
    COLOR_MODE = "warm"
    CUSTOM_COLOR = (255, 100, 50)
    BREATHING_STEPS = 100
    PROGRESS_DELAY_MS = 10
    BREATHING_DELAY_MS = 10

# --- 颜色计算 ---
def get_color(brightness):
    """根据亮度(0-255)和颜色模式返回RGB"""
    if COLOR_MODE == "cold":
        return (brightness, brightness, brightness)  # 冷白
    elif COLOR_MODE == "custom":
        r, g, b = CUSTOM_COLOR
        return (brightness * r // 255, brightness * g // 255, brightness * b // 255)
    else:  # warm
        return (brightness, int(brightness * 0.6), int(brightness * 0.2))  # 暖白

# --- 初始化引脚 ---
# PMOS 是低电平导通，初始化为高电平以保持灯带断电
power_gate = machine.Pin(MOSFET_PIN, machine.Pin.OUT, value=1)
radar = machine.Pin(RADAR_PIN, machine.Pin.IN)
np = neopixel.NeoPixel(machine.Pin(LED_PIN), LED_COUNT)

# --- 配置 GPIO 唤醒源（用于 light sleep 唤醒）---
# 注意：ESP32-C3 的 GPIO 唤醒可能需要特殊配置
# 使用定时唤醒 + 检测引脚状态的方式作为备选方案
USE_GPIO_WAKE = False  # 暂时禁用 GPIO 唤醒，使用定时唤醒

if USE_GPIO_WAKE:
    try:
        wake_mode = getattr(machine, 'WAKE_LIGHT', None)
        if wake_mode is None:
            wake_mode = getattr(machine, 'PIN_WAKE', 4)
        radar.irq(trigger=machine.Pin.IRQ_RISING, wake=wake_mode)
        print(f"GPIO 唤醒配置成功 (wake={wake_mode})")
    except Exception as e:
        print(f"GPIO 唤醒配置失败: {e}")
        USE_GPIO_WAKE = False

def set_all_color(r, g, b):
    """设置所有灯珠颜色"""
    for i in range(LED_COUNT):
        np[i] = (r, g, b)
    np.write()

def progress_bar_effect():
    """进度条效果：每个灯珠逐个点亮"""
    for i in range(LED_COUNT):
        np[i] = get_color(255)
        np.write()
        time.sleep_ms(PROGRESS_DELAY_MS)

def breathing_once():
    """完成一次呼吸效果（亮→暗→亮→暗）"""
    # 亮→暗
    for i in range(BREATHING_STEPS):
        brightness = int((1 - i / BREATHING_STEPS) * 255)
        r, g, b = get_color(brightness)
        set_all_color(r, g, b)
        time.sleep_ms(BREATHING_DELAY_MS)
    # 暗→亮
    for i in range(BREATHING_STEPS):
        brightness = int(i / BREATHING_STEPS * 255)
        r, g, b = get_color(brightness)
        set_all_color(r, g, b)
        time.sleep_ms(BREATHING_DELAY_MS)
    # 亮→暗
    for i in range(BREATHING_STEPS):
        brightness = int((1 - i / BREATHING_STEPS) * 255)
        r, g, b = get_color(brightness)
        set_all_color(r, g, b)
        time.sleep_ms(BREATHING_DELAY_MS)

def off_lights():
    """彻底关闭灯带电源"""
    set_all_color(0, 0, 0) # 先软关闭信号
    power_gate.value(1)    # 切断 PMOS 电源

def on_lights():
    """开启灯带电源"""
    power_gate.value(0)    # PMOS 导通
    time.sleep_ms(50)      # 等待电压稳定

# --- 主循环（低功耗模式）---
print("系统启动，进入低功耗睡眠模式...")
print(f"RADAR_PIN={RADAR_PIN}, 当前状态={radar.value()}")

try:
    while True:
        # 如果引脚已经是高电平，先执行灯效
        if radar.value() == 1:
            print("检测到高电平！执行灯效...")
            on_lights()
            progress_bar_effect()  # 进度条效果
            breathing_once()       # 呼吸效果
            off_lights()           # 关闭灯光
            print("灯效完成，等待下一次触发...")

            # 等待引脚变低，避免重复触发
            print("等待引脚变低...")
            while radar.value() == 1:
                machine.lightsleep(100)  # 每 100ms 检查一次
            print("引脚已变低")

        # 进入睡眠
        if USE_GPIO_WAKE:
            # GPIO 唤醒模式：无限睡眠
            print("进入睡眠，等待 GPIO 唤醒...")
            machine.lightsleep()
        else:
            # 定时唤醒模式：每 100ms 检查一次
            machine.lightsleep(100)

        print(f"唤醒！引脚状态={radar.value()}")

except KeyboardInterrupt:
    print("程序停止")
    off_lights()