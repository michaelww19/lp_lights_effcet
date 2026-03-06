# --- 硬件引脚配置 ---
RADAR_PIN = 2        # LD2410C 的 OUT 引脚
MOSFET_PIN = 4       # AO3401 PMOS 的栅极 (Gate)
LED_PIN = 5          # WS2812B 的数据引脚 (DIN)

# --- LED 配置 ---
LED_COUNT = 29       # 灯珠数量，根据实际修改

# --- 颜色配置 ---
# 可选: "warm" (暖白), "cold" (冷白), "custom" (自定义)
COLOR_MODE = "cold"

# 自定义颜色 (R, G, B)，仅当 COLOR_MODE = "custom" 时生效
CUSTOM_COLOR = (255, 100, 50)

# --- 渐变效果配置 ---
FADE_STEPS = 50             # 渐显/渐隐步数（越大变化越平滑）
FADE_DELAY_MS = 15          # 每步延迟(ms)，值越大渐变越慢
PERSON_LEAVE_DELAY_MS = 2000  # 人离开后延迟(ms)再开始渐隐，避免频繁闪烁

# --- 旧配置（保留兼容，但不再使用）---
BREATHING_STEPS = 100
PROGRESS_DELAY_MS = 10
BREATHING_DELAY_MS = 10
