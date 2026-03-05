# --- 硬件引脚配置 ---
RADAR_PIN = 2        # LD2410C 的 OUT 引脚
MOSFET_PIN = 4       # AO3401 PMOS 的栅极 (Gate)
LED_PIN = 5          # WS2812B 的数据引脚 (DIN)

# --- LED 配置 ---
LED_COUNT = 16       # 灯珠数量，根据实际修改

# --- 颜色配置 ---
# 可选: "warm" (暖白), "cold" (冷白), "custom" (自定义)
COLOR_MODE = "cold"

# 自定义颜色 (R, G, B)，仅当 COLOR_MODE = "custom" 时生效
CUSTOM_COLOR = (255, 100, 50)

# --- 效果配置 ---
BREATHING_STEPS = 100      # 呼吸效果步数（越大越慢）
PROGRESS_DELAY_MS = 10     # 进度条每灯延迟(ms)
BREATHING_DELAY_MS = 10    # 呼吸效果每步延迟(ms)
