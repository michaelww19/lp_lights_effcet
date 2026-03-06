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
        USE_GPIO_WAKE, HOLD_GPIO_STATE
    )
except ImportError:
    # 默认配置
    RADAR_PIN = 2
    MOSFET_PIN = 4
    LED_PIN = 5
    LED_COUNT = 21
    COLOR_MODE = "warm"
    CUSTOM_COLOR = (255, 100, 50)
    FADE_STEPS = 50
    FADE_DELAY_MS = 20
    PERSON_LEAVE_DELAY_MS = 2000
    USE_GPIO_WAKE = True
    HOLD_GPIO_STATE = True  # 保持 GPIO 状态防止 sleep 时丢失

# --- 颜色计算 ---
def get_color(brightness):
    """根据亮度(0-255)和颜色模式返回RGB"""
    if COLOR_MODE == "cold":
        return (brightness, brightness, brightness)
    elif COLOR_MODE == "custom":
        r, g, b = CUSTOM_COLOR
        return (brightness * r // 255, brightness * g // 255, brightness * b // 255)
    else:  # warm
        return (brightness, int(brightness * 0.6), int(brightness * 0.2))

# --- 初始化引脚 ---
# PMOS 是低电平导通，初始化为高电平以保持灯带断电
# 明确禁用上下拉，避免漏电流
power_gate = machine.Pin(MOSFET_PIN, machine.Pin.OUT, value=1, pull=None)
radar = machine.Pin(RADAR_PIN, machine.Pin.IN, pull=None)
np = neopixel.NeoPixel(machine.Pin(LED_PIN), LED_COUNT)

# --- 配置 GPIO 唤醒 ---
# 坑点1: 需要先配置 gpio_wakeup_enable，再配置 wake_on_gpio
if USE_GPIO_WAKE:
    try:
        # 配置雷达引脚为高电平唤醒
        # 注意：ESP32-C3 的 wake_on_gpio 需要 GPIO 模块在 sleep 时保持上电
        esp32.wake_on_gpio((radar,), esp32.WAKEUP_ANY_HIGH)
        print(f"GPIO 唤醒已配置: PIN{RADAR_PIN} 上升沿唤醒")
    except Exception as e:
        print(f"GPIO 唤醒配置失败: {e}")
        USE_GPIO_WAKE = False

# --- 状态变量 ---
current_brightness = 0
last_person_time = time.ticks_ms()
lights_power_on = False

def set_all_brightness(brightness):
    """设置所有灯珠亮度"""
    r, g, b = get_color(brightness)
    for i in range(LED_COUNT):
        np[i] = (r, g, b)
    np.write()

def hold_power_gate():
    """
    坑点2: Light-sleep 时 GPIO 可能变为高阻态
    使用 hold 功能保持 PMOS 控制引脚状态
    """
    if HOLD_GPIO_STATE:
        # 在 ESP32-C3 上，使用 hold 功能保持 GPIO 状态
        # 这可以防止 sleep 期间 GPIO 漂移导致灯带意外亮/灭
        machine.Pin(MOSFET_PIN).hold(True)

def release_power_gate():
    """释放 GPIO hold 状态，允许后续修改"""
    if HOLD_GPIO_STATE:
        machine.Pin(MOSFET_PIN).hold(False)

def power_on_lights():
    """开启灯带电源"""
    global lights_power_on
    if not lights_power_on:
        release_power_gate()  # 先解除 hold 才能修改
        power_gate.value(0)   # PMOS 导通
        time.sleep_ms(50)
        lights_power_on = True
        hold_power_gate()     # 保持状态防止 sleep 时丢失

def power_off_lights():
    """彻底关闭灯带电源"""
    global lights_power_on
    set_all_brightness(0)
    np.write()
    time.sleep_ms(10)
    release_power_gate()
    power_gate.value(1)   # 切断 PMOS 电源
    lights_power_on = False
    hold_power_gate()

def fade_to_brightness(target):
    """从当前亮度渐变到目标亮度"""
    global current_brightness
    
    if current_brightness == target:
        return
    
    step = 1 if target > current_brightness else -1
    step_size = max(1, 255 // FADE_STEPS)
    
    # 渐变过程中需要保持电源控制引脚可修改
    release_power_gate()
    
    while current_brightness != target:
        if step > 0:
            current_brightness = min(target, current_brightness + step_size)
        else:
            current_brightness = max(target, current_brightness - step_size)
        
        set_all_brightness(current_brightness)
        machine.lightsleep(FADE_DELAY_MS)
        
        if step > 0 and current_brightness >= target:
            break
        if step < 0 and current_brightness <= target:
            break
    
    # 渐变完成后保持状态
    hold_power_gate()

def check_person_timeout():
    """
    坑点3: time.ticks_diff 在 lightsleep 后可能不准确
    使用计数器方式辅助判断
    """
    # 简单的超时检测，实际项目中可能需要更复杂的逻辑
    return True

def enter_low_power_mode():
    """
    进入低功耗睡眠模式
    坑点4: 确保 GPIO 状态已保持，避免 sleep 期间灯带意外亮
    """
    # 确保电源控制引脚状态已保持
    hold_power_gate()
    
    if USE_GPIO_WAKE:
        # GPIO 唤醒模式：无限期睡眠
        # 坑点5: 如果 GPIO 唤醒配置不正确，这里会睡死
        machine.lightsleep()
    else:
        # 备用模式：定时唤醒
        machine.lightsleep(100)

# --- 初始化完成后的状态保持 ---
# 初始状态：灯灭，确保状态被保持
hold_power_gate()

# --- 主循环 ---
print("=" * 50)
print("系统启动 - 低功耗渐变感应灯 (改进版)")
print(f"RADAR_PIN={RADAR_PIN}, LED_COUNT={LED_COUNT}")
print(f"GPIO 唤醒: {'已启用' if USE_GPIO_WAKE else '已禁用'}")
print(f"GPIO Hold: {'已启用' if HOLD_GPIO_STATE else '已禁用'}")
print("改进: 修复 GPIO 状态丢失问题")
print("=" * 50)

try:
    while True:
        # 读取雷达状态
        person_detected = radar.value() == 1
        
        # 坑点6: 刚唤醒时可能需要一点时间稳定读取
        # 如果检测到唤醒，等待一小段时间确保状态稳定
        if USE_GPIO_WAKE:
            time.sleep_ms(10)
            person_detected = radar.value() == 1
        
        if person_detected:
            # 检测到人，更新时间戳
            last_person_time = time.ticks_ms()
            
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
                # 坑点7: ticks_diff 在频繁 sleep 后可能不准，增加容错
                elapsed = time.ticks_diff(time.ticks_ms(), last_person_time)
                if elapsed > PERSON_LEAVE_DELAY_MS or elapsed < 0:  # <0 表示溢出
                    print("人已离开，渐灭...")
                    fade_to_brightness(0)
                    print("已熄灭")
                    power_off_lights()
        
        # 低功耗管理
        if current_brightness == 0 and not person_detected:
            # 灯灭了且没检测到人，进入低功耗睡眠
            enter_low_power_mode()
        else:
            # 灯亮着或刚检测到人，使用短暂 lightsleep
            machine.lightsleep(50)

except KeyboardInterrupt:
    print("\n程序停止")
    release_power_gate()
    fade_to_brightness(0)
    power_off_lights()
    print("已清理并退出")
