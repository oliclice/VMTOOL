from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QPushButton, QMessageBox, QHBoxLayout) 
from PyQt6.QtCore import Qt
from app.core.config_manager import config_manager
from ..threads.delete_table_thread import DeleteTableThread, SetAllManualToFalseThread

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
    
    # 分割线
    section_layout.addLayout(delete_table_layout)
    
    # 手动全部为否设置
    manual_false_layout = QVBoxLayout()
    
    # 手动全部为否按钮
    manual_false_chars_button = QPushButton("字表手动全部为否")
    manual_false_chars_button.clicked.connect(lambda: set_all_manual_to_false(parent, dict_service, "chars", "字表"))
    
    manual_false_words_button = QPushButton("词表手动全部为否")
    manual_false_words_button.clicked.connect(lambda: set_all_manual_to_false(parent, dict_service, "words", "词表"))
    
    manual_false_special_button = QPushButton("特殊字符表手动全部为否")
    manual_false_special_button.clicked.connect(lambda: set_all_manual_to_false(parent, dict_service, "special", "特殊字符表"))
    
    manual_false_layout.addWidget(manual_false_chars_button)
    manual_false_layout.addWidget(manual_false_words_button)
    manual_false_layout.addWidget(manual_false_special_button)
    
    section_layout.addLayout(manual_false_layout)
    section_widget.setLayout(section_layout)
    
    settings_content_layout.addWidget(section_widget)
    section_widgets["删除表"] = section_widget

def _get_progress_bar(parent):
    """获取进度条组件"""
    # 尝试不同的属性名
    if hasattr(parent, 'progress_bar'):
        return parent.progress_bar
    if hasattr(parent, 'progress_bar_widget'):
        return parent.progress_bar_widget
    return None

def _refresh_tab(parent, table_name):
    """刷新指定的标签页"""
    tab_map = {
        "chars": ("chars_tab", "refresh_data"),
        "words": ("words_tab", "refresh_data"),
        "special": ("special_tab", "refresh_data")
    }
    
    if table_name not in tab_map:
        return
    
    tab_attr, method_name = tab_map[table_name]
    if hasattr(parent, tab_attr):
        tab = getattr(parent, tab_attr)
        if hasattr(tab, method_name):
            getattr(tab, method_name)()

def delete_table(parent, dict_service, table_name, table_display_name):
    """删除表（异步）"""
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
        # 获取进度条
        progress_bar = _get_progress_bar(parent)
        if progress_bar:
            progress_bar.start_progress(f"正在删除{table_display_name}...")
        
        # 创建并启动线程
        thread = DeleteTableThread(dict_service, table_name, table_display_name)
        
        def on_progress(progress, message):
            if progress_bar:
                progress_bar.update_progress(progress, message)
        
        def on_finished(result):
            if progress_bar:
                progress_bar.finish_progress(f"删除成功，共删除 {result.get('deleted', 0)} 条记录")
            QMessageBox.information(parent, "成功", f"{table_display_name}删除成功")
            # 刷新相关标签页
            _refresh_tab(parent, table_name)
            # 清理线程
            thread.deleteLater()
        
        def on_error(error_msg):
            if progress_bar:
                progress_bar.error_progress(f"删除失败: {error_msg}")
            QMessageBox.critical(parent, "错误", f"删除{table_display_name}失败: {error_msg}")
            # 清理线程
            thread.deleteLater()
        
        thread.progress.connect(on_progress)
        thread.finished.connect(on_finished)
        thread.error.connect(on_error)
        thread.start()

def set_all_manual_to_false(parent, dict_service, table_name, table_display_name):
    """将指定表的所有词条的manual设置为False（异步）"""
    if not dict_service:
        QMessageBox.warning(parent, "警告", "词典服务未初始化")
        return
    
    reply = QMessageBox.question(
        parent, 
        "确认操作", 
        f"确定要将{table_display_name}的所有词条设置为非手动吗？",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    
    if reply == QMessageBox.StandardButton.Yes:
        # 获取进度条
        progress_bar = _get_progress_bar(parent)
        if progress_bar:
            progress_bar.start_progress(f"正在更新{table_display_name}...")
        
        # 创建并启动线程
        thread = SetAllManualToFalseThread(dict_service, table_name, table_display_name)
        
        def on_progress(progress, message):
            if progress_bar:
                progress_bar.update_progress(progress, message)
        
        def on_finished(result):
            if progress_bar:
                progress_bar.finish_progress(f"更新成功，共更新 {result.get('updated', 0)} 条记录")
            QMessageBox.information(parent, "成功", f"{table_display_name}更新成功，共更新 {result.get('updated', 0)} 条记录")
            # 刷新相关标签页
            _refresh_tab(parent, table_name)
            # 清理线程
            thread.deleteLater()
        
        def on_error(error_msg):
            if progress_bar:
                progress_bar.error_progress(f"更新失败: {error_msg}")
            QMessageBox.critical(parent, "错误", f"更新{table_display_name}失败: {error_msg}")
            # 清理线程
            thread.deleteLater()
        
        thread.progress.connect(on_progress)
        thread.finished.connect(on_finished)
        thread.error.connect(on_error)
        thread.start()
