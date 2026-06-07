"""设置模块 - 面板注册和导出"""

from .base_panel import SettingsPanel
from .appearance_panel import AppearancePanel
from .data_panel import DataPanel
from .cache_panel import CachePanel
from .stats_panel import StatsPanel
from .export_panel import ExportPanel
from .code_rules_panel import CodeRulesPanel
from .danger_zone_panel import DangerZonePanel

# 所有面板类（按默认顺序）
PANEL_CLASSES = [
    AppearancePanel,    # 外观设置（主题+语言+字体）
    DataPanel,          # 数据设置（配置目录+数据库）
    CachePanel,         # 缓存设置
    StatsPanel,         # 统计设置
    ExportPanel,        # 导出设置（文件配置+权重）
    CodeRulesPanel,     # 编码规则
    DangerZonePanel,    # 危险操作（删除表）
]

# 面板名称到类的映射
PANEL_MAP = {cls.panel_name: cls for cls in PANEL_CLASSES}

# 默认面板顺序（面板名称列表）
DEFAULT_PANEL_ORDER = [cls.panel_name for cls in PANEL_CLASSES]

__all__ = [
    'SettingsPanel',
    'PANEL_CLASSES',
    'PANEL_MAP',
    'DEFAULT_PANEL_ORDER',
    'AppearancePanel',
    'DataPanel',
    'CachePanel',
    'StatsPanel',
    'ExportPanel',
    'CodeRulesPanel',
    'DangerZonePanel',
]
