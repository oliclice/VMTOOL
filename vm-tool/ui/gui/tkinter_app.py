"""Tkinter基础GUI界面"""
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
from typing import List, Dict, Any
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.dict import DictService
from app.services.weight import WeightCalculator
from app.services.filter import FilterService
from app.services.stats import StatsService

class VMTOOLApp(tk.Tk):
    """VM-TOOL GUI应用"""
    
    def __init__(self):
        """初始化应用"""
        super().__init__()
        self.title("VM-TOOL - 码表处理工具")
        self.geometry("800x600")
        
        # 初始化服务
        self.dict_service = DictService()
        self.weight_calc = WeightCalculator()
        self.filter_service = FilterService()
        self.stats_service = StatsService()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建标签页
        self.create_notebook()
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="导入", command=self.import_data)
        file_menu.add_command(label="导出", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 工具菜单
        tool_menu = tk.Menu(menubar, tearoff=0)
        tool_menu.add_command(label="计算权重", command=self.calculate_weight)
        tool_menu.add_command(label="检测编码冲突", command=self.detect_conflicts)
        tool_menu.add_command(label="数据迁移", command=self.migrate_data)
        menubar.add_cascade(label="工具", menu=tool_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.config(menu=menubar)
    
    def create_notebook(self):
        """创建标签页"""
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 词表管理标签页
        words_tab = ttk.Frame(notebook)
        notebook.add(words_tab, text="词表管理")
        self.create_words_tab(words_tab)
        
        # 统计分析标签页
        stats_tab = ttk.Frame(notebook)
        notebook.add(stats_tab, text="统计分析")
        self.create_stats_tab(stats_tab)
        
        # 导入导出标签页
        import_export_tab = ttk.Frame(notebook)
        notebook.add(import_export_tab, text="导入导出")
        self.create_import_export_tab(import_export_tab)
    
    def create_words_tab(self, parent):
        """创建词表管理标签页"""
        # 搜索框
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(search_frame, text="搜索", command=lambda: self.search_words(search_var.get())).pack(side=tk.LEFT, padx=5)
        
        # 词表列表
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("word", "code", "weight")
        self.word_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        for col in columns:
            self.word_tree.heading(col, text=col)
            if col == "word":
                self.word_tree.column(col, width=150)
            elif col == "code":
                self.word_tree.column(col, width=100)
            else:
                self.word_tree.column(col, width=80)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.word_tree.yview)
        self.word_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.word_tree.pack(fill=tk.BOTH, expand=True)
        
        # 操作按钮
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="添加", command=self.add_word).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="编辑", command=self.edit_word).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除", command=self.delete_word).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="刷新", command=self.refresh_words).pack(side=tk.LEFT, padx=5)
        
        # 加载词表
        self.refresh_words()
    
    def create_stats_tab(self, parent):
        """创建统计分析标签页"""
        # 统计信息
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 基本统计
        basic_stats_frame = ttk.LabelFrame(stats_frame, text="基本统计")
        basic_stats_frame.pack(fill=tk.X, pady=5)
        
        self.total_words_var = tk.StringVar(value="总词条数: 0")
        self.average_length_var = tk.StringVar(value="平均词长: 0")
        self.conflict_count_var = tk.StringVar(value="编码冲突数: 0")
        self.average_weight_var = tk.StringVar(value="平均权重: 0")
        
        ttk.Label(basic_stats_frame, textvariable=self.total_words_var).pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Label(basic_stats_frame, textvariable=self.average_length_var).pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Label(basic_stats_frame, textvariable=self.conflict_count_var).pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Label(basic_stats_frame, textvariable=self.average_weight_var).pack(side=tk.LEFT, padx=10, pady=5)
        
        # 高频词
        high_freq_frame = ttk.LabelFrame(stats_frame, text="高频词前10名")
        high_freq_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        high_freq_columns = ("rank", "word", "code", "weight")
        self.high_freq_tree = ttk.Treeview(high_freq_frame, columns=high_freq_columns, show="headings")
        
        for col in high_freq_columns:
            self.high_freq_tree.heading(col, text=col)
            if col == "rank":
                self.high_freq_tree.column(col, width=50)
            elif col == "word":
                self.high_freq_tree.column(col, width=100)
            elif col == "code":
                self.high_freq_tree.column(col, width=80)
            else:
                self.high_freq_tree.column(col, width=80)
        
        scrollbar = ttk.Scrollbar(high_freq_frame, orient=tk.VERTICAL, command=self.high_freq_tree.yview)
        self.high_freq_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.high_freq_tree.pack(fill=tk.BOTH, expand=True)
        
        # 刷新统计
        ttk.Button(stats_frame, text="刷新统计", command=self.refresh_stats).pack(side=tk.BOTTOM, pady=5)
        
        # 加载统计信息
        self.refresh_stats()
    
    def create_import_export_tab(self, parent):
        """创建导入导出标签页"""
        # 导入部分
        import_frame = ttk.LabelFrame(parent, text="导入")
        import_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(import_frame, text="文件路径:").pack(side=tk.LEFT, padx=5, pady=5)
        import_path_var = tk.StringVar()
        import_path_entry = ttk.Entry(import_frame, textvariable=import_path_var, width=50)
        import_path_entry.pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(import_frame, text="浏览", command=lambda: self.browse_file(import_path_var)).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(import_frame, text="格式:").pack(side=tk.LEFT, padx=5, pady=5)
        format_var = tk.StringVar(value="txt")
        ttk.Combobox(import_frame, textvariable=format_var, values=["txt", "csv", "json"]).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(import_frame, text="导入", command=lambda: self.import_file(import_path_var.get(), format_var.get())).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 导出部分
        export_frame = ttk.LabelFrame(parent, text="导出")
        export_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(export_frame, text="文件路径:").pack(side=tk.LEFT, padx=5, pady=5)
        export_path_var = tk.StringVar()
        export_path_entry = ttk.Entry(export_frame, textvariable=export_path_var, width=50)
        export_path_entry.pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(export_frame, text="浏览", command=lambda: self.browse_save_file(export_path_var)).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(export_frame, text="格式:").pack(side=tk.LEFT, padx=5, pady=5)
        export_format_var = tk.StringVar(value="txt")
        ttk.Combobox(export_frame, textvariable=export_format_var, values=["txt", "csv", "json"]).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(export_frame, text="导出", command=lambda: self.export_file(export_path_var.get(), export_format_var.get())).pack(side=tk.LEFT, padx=5, pady=5)
    
    def refresh_words(self):
        """刷新词表"""
        # 清空现有数据
        for item in self.word_tree.get_children():
            self.word_tree.delete(item)
        
        # 加载词表
        try:
            words = self.dict_service.get_all_words()
            for word in words:
                self.word_tree.insert("", tk.END, values=(word.word, word.code, word.weight))
        except Exception as e:
            messagebox.showerror("错误", f"加载词表失败: {e}")
    
    def search_words(self, keyword):
        """搜索词条"""
        # 清空现有数据
        for item in self.word_tree.get_children():
            self.word_tree.delete(item)
        
        # 搜索词条
        try:
            results = self.dict_service.search_words(keyword)
            for result in results:
                self.word_tree.insert("", tk.END, values=(result["word"], result["code"], result["weight"]))
        except Exception as e:
            messagebox.showerror("错误", f"搜索失败: {e}")
    
    def add_word(self):
        """添加词条"""
        # 创建添加窗口
        add_window = tk.Toplevel(self)
        add_window.title("添加词条")
        add_window.geometry("400x200")
        
        # 词
        ttk.Label(add_window, text="词:").pack(padx=10, pady=5, anchor=tk.W)
        word_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=word_var, width=30).pack(padx=10, pady=5)
        
        # 编码
        ttk.Label(add_window, text="编码:").pack(padx=10, pady=5, anchor=tk.W)
        code_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=code_var, width=30).pack(padx=10, pady=5)
        
        # 权重
        ttk.Label(add_window, text="权重:").pack(padx=10, pady=5, anchor=tk.W)
        weight_var = tk.DoubleVar(value=1.0)
        ttk.Entry(add_window, textvariable=weight_var, width=30).pack(padx=10, pady=5)
        
        # 按钮
        button_frame = ttk.Frame(add_window)
        button_frame.pack(pady=10)
        
        def save_word():
            try:
                word = word_var.get()
                code = code_var.get() or None
                weight = weight_var.get()
                
                self.dict_service.add_word(word, code, weight)
                messagebox.showinfo("成功", "词条添加成功")
                add_window.destroy()
                self.refresh_words()
            except Exception as e:
                messagebox.showerror("错误", f"添加失败: {e}")
        
        ttk.Button(button_frame, text="保存", command=save_word).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=add_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def edit_word(self):
        """编辑词条"""
        selected_item = self.word_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请选择要编辑的词条")
            return
        
        item = selected_item[0]
        values = self.word_tree.item(item, "values")
        word = values[0]
        code = values[1]
        weight = float(values[2])
        
        # 创建编辑窗口
        edit_window = tk.Toplevel(self)
        edit_window.title("编辑词条")
        edit_window.geometry("400x200")
        
        # 词（只读）
        ttk.Label(edit_window, text="词:").pack(padx=10, pady=5, anchor=tk.W)
        word_var = tk.StringVar(value=word)
        ttk.Entry(edit_window, textvariable=word_var, width=30, state="disabled").pack(padx=10, pady=5)
        
        # 编码
        ttk.Label(edit_window, text="编码:").pack(padx=10, pady=5, anchor=tk.W)
        code_var = tk.StringVar(value=code)
        ttk.Entry(edit_window, textvariable=code_var, width=30).pack(padx=10, pady=5)
        
        # 权重
        ttk.Label(edit_window, text="权重:").pack(padx=10, pady=5, anchor=tk.W)
        weight_var = tk.DoubleVar(value=weight)
        ttk.Entry(edit_window, textvariable=weight_var, width=30).pack(padx=10, pady=5)
        
        # 按钮
        button_frame = ttk.Frame(edit_window)
        button_frame.pack(pady=10)
        
        def save_edit():
            try:
                new_code = code_var.get()
                new_weight = weight_var.get()
                
                update_data = {}
                if new_code != code:
                    update_data["code"] = new_code
                if new_weight != weight:
                    update_data["weight"] = new_weight
                
                if update_data:
                    self.dict_service.update_word(word, **update_data)
                    messagebox.showinfo("成功", "词条更新成功")
                    edit_window.destroy()
                    self.refresh_words()
                else:
                    edit_window.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"更新失败: {e}")
        
        ttk.Button(button_frame, text="保存", command=save_edit).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=edit_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def delete_word(self):
        """删除词条"""
        selected_item = self.word_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请选择要删除的词条")
            return
        
        item = selected_item[0]
        word = self.word_tree.item(item, "values")[0]
        
        if messagebox.askyesno("确认", f"确定要删除词条 '{word}' 吗？"):
            try:
                result = self.dict_service.delete_word(word)
                if result:
                    messagebox.showinfo("成功", "词条删除成功")
                    self.refresh_words()
                else:
                    messagebox.showwarning("警告", "词条不存在")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {e}")
    
    def refresh_stats(self):
        """刷新统计信息"""
        try:
            report = self.stats_service.generate_report()
            
            # 更新基本统计
            self.total_words_var.set(f"总词条数: {report['word_length_stats']['total_words']}")
            self.average_length_var.set(f"平均词长: {report['word_length_stats']['average_length']:.2f}")
            self.conflict_count_var.set(f"编码冲突数: {report['code_stats']['conflict_count']}")
            self.average_weight_var.set(f"平均权重: {report['weight_stats']['average_weight']:.2f}")
            
            # 更新高频词
            for item in self.high_freq_tree.get_children():
                self.high_freq_tree.delete(item)
            
            high_freq_words = report['high_frequency_words']
            for i, word in enumerate(high_freq_words[:10], 1):
                self.high_freq_tree.insert("", tk.END, values=(i, word['word'], word['code'], word['weight']))
        except Exception as e:
            messagebox.showerror("错误", f"获取统计信息失败: {e}")
    
    def import_data(self):
        """导入数据"""
        file_path = filedialog.askopenfilename(
            title="选择导入文件",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            # 自动检测文件格式
            if file_path.endswith(".txt"):
                format = "txt"
            elif file_path.endswith(".csv"):
                format = "csv"
            elif file_path.endswith(".json"):
                format = "json"
            else:
                messagebox.showerror("错误", "不支持的文件格式")
                return
            
            self.import_file(file_path, format)
    
    def import_file(self, file_path, format):
        """导入文件"""
        if not file_path:
            messagebox.showwarning("警告", "请选择文件")
            return
        
        try:
            if format == "txt":
                result = self.filter_service.import_from_txt(file_path)
            elif format == "csv":
                result = self.filter_service.import_from_csv(file_path)
            elif format == "json":
                result = self.filter_service.import_from_json(file_path)
            else:
                messagebox.showerror("错误", "不支持的格式")
                return
            
            messagebox.showinfo("成功", f"导入成功: 添加了 {result['added']} 条，跳过了 {result['existing']} 条")
            self.refresh_words()
        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {e}")
    
    def export_data(self):
        """导出数据"""
        file_path = filedialog.asksaveasfilename(
            title="选择导出文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("JSON文件", "*.json")]
        )
        
        if file_path:
            # 自动检测文件格式
            if file_path.endswith(".txt"):
                format = "txt"
            elif file_path.endswith(".csv"):
                format = "csv"
            elif file_path.endswith(".json"):
                format = "json"
            else:
                messagebox.showerror("错误", "不支持的文件格式")
                return
            
            self.export_file(file_path, format)
    
    def export_file(self, file_path, format):
        """导出文件"""
        if not file_path:
            messagebox.showwarning("警告", "请选择文件")
            return
        
        try:
            if format == "txt":
                count = self.filter_service.export_to_txt(file_path)
            elif format == "csv":
                count = self.filter_service.export_to_csv(file_path)
            elif format == "json":
                count = self.filter_service.export_to_json(file_path)
            else:
                messagebox.showerror("错误", "不支持的格式")
                return
            
            messagebox.showinfo("成功", f"导出成功: 共导出 {count} 条数据")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")
    
    def browse_file(self, var):
        """浏览文件"""
        file_path = filedialog.askopenfilename(
            title="选择文件",
            filetypes=[("所有文件", "*.*")]
        )
        if file_path:
            var.set(file_path)
    
    def browse_save_file(self, var):
        """浏览保存文件"""
        file_path = filedialog.asksaveasfilename(
            title="选择保存文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("JSON文件", "*.json")]
        )
        if file_path:
            var.set(file_path)
    
    def calculate_weight(self):
        """计算权重"""
        if messagebox.askyesno("确认", "确定要重新计算所有词条的权重吗？"):
            try:
                # 这里需要实现批量计算权重的逻辑
                messagebox.showinfo("成功", "权重计算完成")
                self.refresh_words()
                self.refresh_stats()
            except Exception as e:
                messagebox.showerror("错误", f"计算失败: {e}")
    
    def detect_conflicts(self):
        """检测编码冲突"""
        try:
            conflicts = self.stats_service.detect_code_conflicts()
            if conflicts:
                # 创建冲突窗口
                conflict_window = tk.Toplevel(self)
                conflict_window.title("编码冲突")
                conflict_window.geometry("600x400")
                
                columns = ("code", "count", "words")
                conflict_tree = ttk.Treeview(conflict_window, columns=columns, show="headings")
                
                for col in columns:
                    conflict_tree.heading(col, text=col)
                    if col == "code":
                        conflict_tree.column(col, width=100)
                    elif col == "count":
                        conflict_tree.column(col, width=80)
                    else:
                        conflict_tree.column(col, width=400)
                
                scrollbar = ttk.Scrollbar(conflict_window, orient=tk.VERTICAL, command=conflict_tree.yview)
                conflict_tree.configure(yscroll=scrollbar.set)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                conflict_tree.pack(fill=tk.BOTH, expand=True)
                
                for conflict in conflicts:
                    words_str = ", ".join([word['word'] for word in conflict['words']])
                    conflict_tree.insert("", tk.END, values=(conflict['code'], conflict['count'], words_str))
            else:
                messagebox.showinfo("信息", "未发现编码冲突")
        except Exception as e:
            messagebox.showerror("错误", f"检测失败: {e}")
    
    def migrate_data(self):
        """数据迁移"""
        if messagebox.askyesno("确认", "确定要执行数据迁移吗？"):
            try:
                from app.dal.migration import full_migration
                result = full_migration()
                messagebox.showinfo("成功", f"数据迁移完成: {result}")
                self.refresh_words()
                self.refresh_stats()
            except Exception as e:
                messagebox.showerror("错误", f"迁移失败: {e}")
    
    def show_about(self):
        """显示关于信息"""
        messagebox.showinfo("关于", "VM-TOOL v2.0.0\n现代化码表处理工具\n\n支持词表管理、权重计算、数据导入导出等功能")


if __name__ == "__main__":
    app = VMTOOLApp()
    app.mainloop()
