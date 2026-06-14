"""QSS 变量替换引擎

将 QSS 中的 @variable 占位符替换为 ColorPalette 的实际值。
"""
import dataclasses
from app.core.theme_config import ColorPalette


def resolve_qss_variables(qss: str, palette: ColorPalette) -> str:
    """将 QSS 中所有 @variable 替换为 ColorPalette 的实际值

    Args:
        qss: 包含 @variable 占位符的 QSS 字符串
        palette: 当前主题的 ColorPalette 实例

    Returns:
        替换后的纯值 QSS 字符串
    """
    # 将 ColorPalette 的所有字段映射为 @field_name -> value
    variables = {}
    for dc_field in dataclasses.fields(palette):
        value = getattr(palette, dc_field.name)
        if isinstance(value, int):
            value = f"{value}px"
        variables[f"@{dc_field.name}"] = value

    result = qss
    # 按变量名长度降序排序，避免短变量名先替换导致长变量名被截断
    # 例如 @sidebar_text_active 必须在 @sidebar_text 之前替换
    for var_name, var_value in sorted(variables.items(), key=lambda x: len(x[0]), reverse=True):
        result = result.replace(var_name, var_value)

    return result
