"""主题相关常量定义"""

# 主题模式常量
THEME_MODE_AUTO = "auto"
THEME_MODE_LIGHT = "light"
THEME_MODE_DARK = "dark"

# 主题名称常量
THEME_NAME_CLASSIC = "经典"
THEME_NAME_MATERIAL3 = "Material3"
THEME_NAME_LINEAR = "Linear"

# 主题颜色常量
THEME_COLOR_BLUE = "蓝色"
THEME_COLOR_GREEN = "绿色"
THEME_COLOR_RED = "红色"
THEME_COLOR_PURPLE = "紫色"
THEME_COLOR_ORANGE = "橙色"

# 模式显示名称映射
MODE_DISPLAY_MAP = {
    THEME_MODE_AUTO: "跟随系统",
    THEME_MODE_LIGHT: "浅色",
    THEME_MODE_DARK: "深色"
}

# 反向映射：显示名称到内部值
MODE_DISPLAY_REVERSE_MAP = {
    "跟随系统": THEME_MODE_AUTO,
    "浅色": THEME_MODE_LIGHT,
    "深色": THEME_MODE_DARK
}

# 颜色RGB值映射 (R, G, B)
COLOR_RGB_MAP = {
    THEME_COLOR_BLUE: (50, 150, 250),
    THEME_COLOR_GREEN: (50, 150, 100),
    THEME_COLOR_RED: (200, 50, 50),
    THEME_COLOR_PURPLE: (150, 50, 200),
    THEME_COLOR_ORANGE: (200, 100, 50)
}

# 默认主题配置
DEFAULT_THEME_MODE = THEME_MODE_AUTO
DEFAULT_THEME_NAME = THEME_NAME_CLASSIC
DEFAULT_THEME_COLOR = THEME_COLOR_BLUE

# Tab位置常量
TAB_POSITION_TOP = "top"
TAB_POSITION_LEFT = "left"

# Tab位置显示名称映射
TAB_POSITION_DISPLAY_MAP = {
    TAB_POSITION_TOP: "顶部",
    TAB_POSITION_LEFT: "左侧"
}

# 反向映射
TAB_POSITION_DISPLAY_REVERSE_MAP = {
    "顶部": TAB_POSITION_TOP,
    "左侧": TAB_POSITION_LEFT
}

# 默认Tab位置
DEFAULT_TAB_POSITION = TAB_POSITION_TOP

# Tab 图标映射 (Unicode 字符)
TAB_ICONS: dict[str, str] = {
    "chars": "字",       # 字表管理
    "special": "◆",       # 特殊表管理
    "words": "词",        # 词表管理
    "stats": "📊",        # 统计分析
    "import_export": "⇄", # 导入导出
    "code_rules": "{ }",  # 编码规则
    "settings": "⚙",     # 设置
}

# Tab 分组定义: {tab_index: group_label}
# tab_index 对应 addTab 的顺序:
#   0: chars, 1: special, 2: words, 3: stats, 4: import_export, 5: code_rules, 6: settings
TAB_GROUPS: dict[int, str] = {
    0: "数据管理",   # tabs 0-2
    3: "工具",       # tabs 3-5
}
# tab 6 (设置) 不属于任何分组，用视觉分隔线隔离