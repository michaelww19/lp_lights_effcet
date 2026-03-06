import machine
import esp32
import neopixel
import time

# --- 加载配置 ---
try:
    from config import (
        RADAR_PIN, MOSFET_PIN, LED_PIN, LED_COUNT,
        COLOR_MODE, CUSTOM_COLOR,
        FADE_STEPS, FADE_DELAY_MS, PERSON_LEAVE_DELAY_MS,
        USE_GPIO_WAKE
    )
except ImportError:
    # 默认配置（如果没有 config.py）
    RADAR_PIN = 2
    MOSFET_PIN = 4
    LED_PIN = 5
    LED_COUNT = 21
    COLOR_MODE = "warm"
    CUSTOM_COLOR = (255, 100, 50)
    FADE_STEPS = 50        # 渐显/渐隐步数
    FADE_DELAY_MS = 20     # 每步延迟(ms)，值越大越慢
    PERSON_LEAVE_DELAY_MS = 2000  # 人离开后延迟(ms)再开始渐隐
    USE_GPIO_WAKE = True   # 默认启用 GPIO 唤醒

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

# --- 配置 GPIO 唤醒 ---
if USE_GPIO_WAKE:
    try:
        # ESP32-C3 支持 wake_on_gpio 或 wake_on_ext0
        # 配置雷达引脚上升沿唤醒
        esp32.wake_on_gpio((radar,), esp32.WAKEUP_ANY_HIGH)
        print(f"GPIO 唤醒已配置: PIN{RADAR_PIN} 上升沿唤醒")
    except Exception as e:
        print(f"GPIO 唤醒配置失败: {e}")
        USE_GPIO_WAKE = False

# --- 状态变量 ---
current_brightness = 0      # 当前亮度 (0-255)
last_person_time = 0        # 最后检测到人时间
lights_power_on = False     # 灯带电源是否开启

def set_all_brightness(brightness):
    """设置所有灯珠亮度 (0-255)"""
    r, g, b = get_color(brightness)
    for i in range(LED_COUNT):
        np[i] = (r, g, b)
    np.write()

def power_on_lights():
    """开启灯带电源"""
    global lights_power_on
    if not lights_power_on:
        power_gate.value(0)    # PMOS 导通
        time.sleep_ms(50)      # 等待电压稳定
        lights_power_on = True

def power_off_lights():
    """彻底关闭灯带电源"""
    global lights_power_on
    set_all_brightness(0)      # 先清零灯珠
    np.write()
    time.sleep_ms(10)
    power_gate.value(1)        # 切断 PMOS 电源
    lights_power_on = False

def fade_to_brightness(target):
    """
    从当前亮度渐变到目标亮度
    target: 0-255
    """
    global current_brightness
    
    if current_brightness == target:
        return
    
    step = 1 if target > current_brightness else -1
    step_size = max(1, 255 // FADE_STEPS)  # 每步调整的亮度值
    
    while current_brightness != target:
        # 计算下一步亮度
        if step > 0:
            current_brightness = min(target, current_brightness + step_size)
        else:
            current_brightness = max(target, current_brightness - step_size)
        
        # 设置亮度
        set_all_brightness(current_brightness)
        
        # 延迟 - 使用 lightsleep 节省功耗
        machine.lightsleep(FADE_DELAY_MS)
        
        # 检查是否到达目标
        if step > 0 and current_brightness >= target:
            break
        if step < 0 and current_brightness <= target:
            break

def enter_low_power_mode():
    """
    进入低功耗睡眠模式
    - 如果启用 GPIO 唤醒：无限期睡眠，等待雷达触发
    - 否则：定时唤醒检查
    """
    if USE_GPIO_WAKE:
        # GPIO 唤醒模式：无限期睡眠，等待雷达上升沿
        # 功耗约 1-5mA，比轮询降低 95%+
        machine.lightsleep()
    else:
        # 备用模式：每 100ms 定时唤醒检查
        machine.lightsleep(100)

# --- 主循环 ---
print("=" * 40)
print("系统启动 - 低功耗渐变感应灯")
print(f"RADAR_PIN={RADAR_PIN}, LED_COUNT={LED_COUNT}")
print(f"GPIO 唤醒: {'已启用' if USE_GPIO_WAKE else '已禁用'}")
print("功能: 人来渐亮，人走渐灭，空闲时自动休眠")
print("=" * 40)

try:
    while True:
        # 读取雷达状态
        person_detected = radar.value() == 1
        current_time = time.ticks_ms()
        
        if person_detected:
            # 检测到人
            last_person_time = current_time
            
            # 确保电源开启
            if not lights_power_on:
                power_on_lights()
            
            # 如果当前不是最亮，渐亮
            if current_brightness < 255:
                print("检测到有人，渐亮...")
                fade_to_brightness(255)
                print("已最亮")
        else:
            # 没检测到人
            if current_brightness > 0:
                # 检查是否过了延迟时间
                if time.ticks_diff(current_time, last_person_time) > PERSON_LEAVE_DELAY_MS:
                    print("人已离开，渐灭...")
                    fade_to_brightness(0)
                    print("已熄灭")
                    power_off_lights()
        
        # 低功耗管理
        if current_brightness == 0 and not person_detected:
            # 灯灭了且没检测到人，进入低功耗睡眠
            # 等待 GPIO 唤醒或定时唤醒
            enter_low_power_mode()
        else:
            # 灯亮着或刚检测到人，使用短暂 lightsleep 节省 CPU
            machine.lightsleep(50)

except KeyboardInterrupt:
    print("\n程序停止")
    fade_to_brightness(0)
    power_off_lights()
    print("已清理并退出")
