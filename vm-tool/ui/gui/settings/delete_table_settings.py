from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QPushButton, QMessageBox) 
from PyQt6.QtCore import Qt
from app.core.config_manager import config_manager

def load_delete_table_settings(settings_content_layout, section_widgets, parent, dict_service):
    """加载删除表设置"""
    section_widget = QGroupBox("删除表")
    section_layout = QVBoxLayout()
    
    # 删除表设置
    delete_table_layout = QVBoxLayout()
    
    # 删除字表按钮
    delete_chars_button = QPushButton("删除字表")
    delete_chars_button.clicked.connect(lambda: delete_table(parent, dict_service, "chars", "字表"))
    
    # 删除词表按钮
    delete_words_button = QPushButton("删除词表")
    delete_words_button.clicked.connect(lambda: delete_table(parent, dict_service, "words", "词表"))
    
    # 删除特殊字符表按钮
    delete_special_button = QPushButton("删除特殊字符表")
    delete_special_button.clicked.connect(lambda: delete_table(parent, dict_service, "special", "特殊字符表"))
    
    delete_table_layout.addWidget(delete_chars_button)
    delete_table_layout.addWidget(delete_words_button)
    delete_table_layout.addWidget(delete_special_button)
    
    section_layout.addLayout(delete_table_layout)
    section_widget.setLayout(section_layout)
    
    settings_content_layout.addWidget(section_widget)
    section_widgets["删除表"] = section_widget

def delete_table(parent, dict_service, table_name, table_display_name):
    """删除表"""
    if not dict_service:
        QMessageBox.warning(parent, "警告", "词典服务未初始化")
        return
    
    reply = QMessageBox.question(
        parent, 
        "确认删除", 
        f"确定要删除{table_display_name}吗？此操作不可恢复！",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    
    if reply == QMessageBox.StandardButton.Yes:
        try:
            dict_service.delete_table(table_name)
            QMessageBox.information(parent, "成功", f"{table_display_name}删除成功")
            # 刷新相关标签页
            if hasattr(parent, f"refresh_{table_name}"):
                getattr(parent, f"refresh_{table_name}")()
        except Exception as e:
            QMessageBox.critical(parent, "错误", f"删除{table_display_name}失败: {e}")
