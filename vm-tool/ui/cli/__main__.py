"""VM-TOOL 命令行界面"""
import typer
import click
import io
import sys
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from typing import List, Optional

from app.services.dict import DictService
from app.services.weight import WeightCalculator
from app.services.filter import FilterService
from app.services.stats import StatsService
from app.core.compatibility import CompatibilityLayer

console = Console()
app = typer.Typer(
    name="vm-tool",
    help="码表处理工具",
    add_completion=True,
    no_args_is_help=False
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """码表处理工具"""
    if ctx.invoked_subcommand is None:
        # 没有指定命令，进入交互式模式
        console.print("[bold cyan]VM-TOOL 交互式模式[/bold cyan]")
        console.print("输入 'help' 查看可用命令，输入 'exit/quit' 退出")
        
        # 自动显示命令列表
        show_typer_help()
        
        while True:
            command = Prompt.ask("\n请输入命令")
            
            if command == "exit" or command == "quit":
                console.print("[green]再见！[/green]")
                break
            elif command == "help":
                show_typer_help()
            else:
                # 使用 Typer 执行命令
                parts = command.split()
                if not parts:
                    continue

                try:
                    from click.testing import CliRunner
                    from typer.main import get_command
                    cmd = get_command(app)
                    runner = CliRunner()
                    result = runner.invoke(cmd, parts)
                    if result.output:
                        console.print(result.output)
                    if result.exception:
                        raise result.exception
                except Exception as e:
                    console.print(f"[red]执行命令失败:[/red] {e}")

# 延迟初始化服务，避免全局初始化导致的数据库冲突
dict_service = None
weight_calc = None
filter_service = None
stats_service = None
compatibility = None


def get_services():
    """获取服务实例"""
    global dict_service, weight_calc, filter_service, stats_service, compatibility
    if dict_service is None:
        dict_service = DictService()
        weight_calc = WeightCalculator()
        filter_service = FilterService()
        stats_service = StatsService()
        compatibility = CompatibilityLayer()
    return dict_service, weight_calc, filter_service, stats_service, compatibility


@app.command("add")
def add_word(word: str, code: Optional[str] = None, weight: float = 1.0, is_character: Optional[bool] = None):
    """添加词条"""
    try:
        dict_service, _, _, _, _ = get_services()
        result = dict_service.add_word(word, code, weight, is_character)
        console.print(f"[green]添加成功:[/green] {result}")
    except Exception as e:
        console.print(f"[red]添加失败:[/red] {e}")








@app.command("delete")
def delete_word(word: str):
    """删除词条"""
    try:
        dict_service, _, _, _, _ = get_services()
        result = dict_service.delete_word(word)
        if result:
            console.print(f"[green]删除成功:[/green] {word}")
        else:
            console.print(f"[yellow]删除失败:[/yellow] 词条不存在")
    except Exception as e:
        console.print(f"[red]删除失败:[/red] {e}")


@app.command("delete-batch")
def delete_batch(words: List[str]):
    """批量删除词条"""
    try:
        dict_service, _, _, _, _ = get_services()
        result = dict_service.delete_words(words)
        console.print(f"[green]批量删除完成:[/green] 删除了 {result['deleted']} 条，{result['not_found']} 条不存在")
        if result['not_found_words']:
            console.print(f"[yellow]不存在的词条:[/yellow] {result['not_found_words']}")
    except Exception as e:
        console.print(f"[red]批量删除失败:[/red] {e}")


@app.command("query")
def query_word(keyword: str):
    """查询词条"""
    try:
        dict_service, _, _, _, _ = get_services()
        results = dict_service.search_words(keyword)
        if results:
            table = Table(title="查询结果")
            table.add_column("词", style="cyan")
            table.add_column("编码", style="green")
            table.add_column("权重", style="yellow")
            
            for result in results:
                table.add_row(result["word"], result["code"], str(result["weight"]))
            
            console.print(table)
        else:
            console.print(f"[yellow]未找到匹配的词条:[/yellow] {keyword}")
    except Exception as e:
        console.print(f"[red]查询失败:[/red] {e}")


@app.command("set-weight")
def set_weight(word: str, weight: float):
    """设置词条权重"""
    try:
        _, weight_calc, _, _, _ = get_services()
        result = weight_calc.set_weight_directly(word, weight)
        console.print(f"[green]设置权重成功:[/green] {result}")
    except Exception as e:
        console.print(f"[red]设置权重失败:[/red] {e}")


@app.command("replace-code")
def replace_code(word: str, new_code: str):
    """替换词条编码"""
    try:
        dict_service, _, _, _, _ = get_services()
        result = dict_service.replace_code(word, new_code)
        console.print(f"[green]替换编码成功:[/green] {result}")
    except Exception as e:
        console.print(f"[red]替换编码失败:[/red] {e}")


@app.command("calculate-all-codes")
def calculate_all_codes(rule: str = "first_letter", separator: str = "", max_length: int = 10):
    """计算所有未手动修改过编码的词条的编码
    
    Args:
        rule: 编码规则 (first_letter, all_letters, custom)
        separator: 编码分隔符
        max_length: 最大编码长度
    """
    try:
        dict_service, _, _, _, _ = get_services()
        # 设置编码生成配置
        config = {
            'rule': rule,
            'separator': separator,
            'max_length': max_length
        }
        dict_service.code_generator.set_config(config)
        
        # 获取总数用于进度条
        from app.dal.models import Word
        total = dict_service.db.query(Word).filter(Word.manual == False, Word.is_character == False).count()
        
        if total == 0:
            console.print("[yellow]没有需要计算编码的词条[/yellow]")
            return
        
        # 使用Rich进度条
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]计算编码中...", total=total)
            
            # 定义进度回调函数
            def progress_callback(percentage: int, message: str):
                # 根据百分比更新进度条
                completed = int(total * percentage / 100)
                progress.update(task, completed=completed, description=f"[cyan]{message}[/cyan]")
            
            # 批量计算编码
            result = dict_service.calculate_all_codes(progress_callback=progress_callback)
        
        console.print(f"[green]批量计算编码完成:[/green]")
        console.print(f"总词条数: {result['total']}")
        console.print(f"成功更新: {result['updated']}")
        console.print(f"更新失败: {result['failed']}")
    except Exception as e:
        console.print(f"[red]批量计算编码失败:[/red] {e}")


@app.command("stats")
def show_stats():
    """显示统计信息"""
    try:
        _, _, _, stats_service, _ = get_services()
        report = stats_service.generate_report()
        
        # 显示词长统计
        console.print("[bold cyan]词长统计[/bold cyan]")
        length_stats = report["word_length_stats"]
        console.print(f"总词条数: {length_stats['total_words']}")
        console.print(f"平均词长: {length_stats['average_length']:.2f}")
        console.print("词长分布:")
        for length, count in length_stats['length_distribution'].items():
            console.print(f"  {length}字: {count}条")
        
        # 显示编码统计
        console.print("\n[bold cyan]编码统计[/bold cyan]")
        code_stats = report["code_stats"]
        console.print(f"总编码数: {code_stats['total_codes']}")
        console.print(f"编码冲突数: {code_stats['conflict_count']}")
        
        # 显示高频词
        console.print("\n[bold cyan]高频词前20名[/bold cyan]")
        high_freq_words = report["high_frequency_words"]
        table = Table()
        table.add_column("排名", style="cyan")
        table.add_column("词", style="green")
        table.add_column("编码", style="yellow")
        table.add_column("权重", style="magenta")
        
        for i, word in enumerate(high_freq_words[:20], 1):
            table.add_row(str(i), word["word"], word["code"], str(word["weight"]))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]获取统计信息失败:[/red] {e}")


@app.command("import")
def import_data(
    file: Optional[str] = typer.Option(None, help="导入文件路径（当导入文件时使用）"),
    words: Optional[List[str]] = typer.Argument(None)
):
    """导入数据
    
    Args:
        file: 导入文件路径（当导入文件时使用）
        words: 批量导入的词条列表（当直接导入词条时使用）
    """
    try:
        dict_service, _, filter_service, _, _ = get_services()
        from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn
        
        # 处理批量导入词条的情况
        if words:
            word_data = []
            for word in words:
                # 简单处理，实际应用中可能需要更复杂的解析
                word_data.append({"word": word, "code": None, "weight": 1.0})
            
            with Progress(
                TextColumn("[bold cyan]{task.description}[/bold cyan]"),
                BarColumn(),
                "[green]{task.percentage:>3.0f}%[/green]",
                TimeRemainingColumn(),
            ) as progress:
                progress_task = progress.add_task("开始批量添加...", total=100)
                
                def progress_callback(progress_val, message):
                    progress.update(progress_task, completed=progress_val, description=message)
                
                result = dict_service.add_words(word_data, progress_callback=progress_callback)
            
            console.print(f"[green]批量添加完成:[/green] 添加了 {result['added']} 条，跳过了 {result['existing']} 条")
        # 处理从文件导入的情况
        elif file:
            import os
            # 自动识别文件格式
            _, ext = os.path.splitext(file)
            format = ext[1:].lower() if ext else "txt"
            
            with Progress(
                TextColumn("[bold cyan]{task.description}[/bold cyan]"),
                BarColumn(),
                "[green]{task.percentage:>3.0f}%[/green]",
                TimeRemainingColumn(),
            ) as progress:
                progress_task = progress.add_task("开始导入...", total=100)
                
                def progress_callback(progress_val, message):
                    progress.update(progress_task, completed=progress_val, description=message)
                
                if format == "txt":
                    result = filter_service.import_from_txt(file, progress_callback=progress_callback)
                elif format == "csv":
                    result = filter_service.import_from_csv(file, progress_callback=progress_callback)
                elif format == "json":
                    result = filter_service.import_from_json(file, progress_callback=progress_callback)
                else:
                    console.print(f"[red]不支持的格式:[/red] {format}")
                    return
            
            # 显示导入数据条数和用时
            total_time = result.get('total_time', 0)
            avg_time_per_1000 = result.get('avg_time_per_1000', 0)
            total_count = result.get('total_count', 0)
            
            console.print(f"[green]导入成功:[/green]")
            console.print(f"  添加了: {result['added']} 条")
            console.print(f"  跳过了: {result['existing']} 条")
            console.print(f"  总数据量: {total_count} 条")
            console.print(f"  总耗时: {total_time:.2f} 秒")
            console.print(f"  每千条平均耗时: {avg_time_per_1000:.2f} 秒")
        else:
            console.print(f"[red]错误: 请提供文件路径或词条列表[/red]")
    except Exception as e:
        console.print(f"[red]导入失败:[/red] {e}")


@app.command("export")
def export_data(output_file: Optional[str] = None, format: Optional[str] = None):
    """导出数据"""
    try:
        dict_service, _, _, _, _ = get_services()
        from app.core.config_manager import config_manager
        import os
        
        # 获取导出配置
        export_path = config_manager.get("default_export_path", "./")
        default_format = config_manager.get("default_export_format", "txt")
        
        # 如果没有指定输出文件，使用默认配置
        if not output_file:
            # 确保导出路径存在
            if not os.path.exists(export_path):
                try:
                    os.makedirs(export_path)
                except Exception as e:
                    console.print(f"[red]创建导出目录失败:[/red] {e}")
                    return
            
            # 使用默认格式
            if not format:
                format = default_format
        else:
            # 如果指定了输出文件，从文件扩展名推断格式（如果未指定）
            if not format:
                _, ext = os.path.splitext(output_file)
                format = ext[1:].lower() if ext else "txt"
            
            # 从输出文件路径中提取导出路径
            export_path = os.path.dirname(output_file)
        
        # 确保格式是有效的
        if format not in ["txt", "csv", "json"]:
            console.print(f"[red]不支持的格式:[/red] {format}")
            return
        
        # 检查是否只导出词表
        only_export_words = config_manager.get("only_export_words", False)
        
        # 检查是否启用分表导出
        if config_manager.get("split_export_enabled", False) and not only_export_words:
            # 分表导出（不启用只导出词表时）
            total_exported = 0
            
            # 导出词表
            words_export_name = config_manager.get("words_export_name", "vmtool_words")
            words_file_path = os.path.join(export_path, f"{words_export_name}.{format}")
            words_result = dict_service.export_data(words_file_path, format, table="words")
            total_exported += words_result
            console.print(f"[green]词表导出成功:[/green] 共导出 {words_result} 条数据")
            
            # 导出字表
            chars_export_name = config_manager.get("chars_export_name", "vmtool_chars")
            chars_file_path = os.path.join(export_path, f"{chars_export_name}.{format}")
            chars_result = dict_service.export_data(chars_file_path, format, table="chars")
            total_exported += chars_result
            console.print(f"[green]字表导出成功:[/green] 共导出 {chars_result} 条数据")
            
            # 导出特殊字符表
            special_export_name = config_manager.get("special_export_name", "vmtool_special")
            special_file_path = os.path.join(export_path, f"{special_export_name}.{format}")
            special_result = dict_service.export_data(special_file_path, format, table="special")
            total_exported += special_result
            console.print(f"[green]特殊字符表导出成功:[/green] 共导出 {special_result} 条数据")
            
            # 检查是否需要自动导出到 Rime 目录
            if config_manager.get("auto_export_ibus_rime", False):
                ibus_rime_path = os.path.expanduser("~/.config/ibus/rime")
                if os.path.exists(ibus_rime_path):
                    # 复制文件到 ibus/rime 目录
                    try:
                        import shutil
                        shutil.copy(words_file_path, ibus_rime_path)
                        console.print(f"[green]自动导出到 ibus/rime 目录成功[/green]")
                    except Exception as e:
                        console.print(f"[yellow]自动导出到 ibus/rime 目录失败:[/yellow] {e}")
            
            if config_manager.get("auto_export_fcitx5_rime", False):
                fcitx5_rime_path = os.path.expanduser("~/.local/share/fcitx5/rime")
                if os.path.exists(fcitx5_rime_path):
                    # 复制文件到 fcitx5/rime 目录
                    try:
                        import shutil
                        shutil.copy(words_file_path, fcitx5_rime_path)
                        console.print(f"[green]自动导出到 fcitx5/rime 目录成功[/green]")
                    except Exception as e:
                        console.print(f"[yellow]自动导出到 fcitx5/rime 目录失败:[/yellow] {e}")
            
            console.print(f"[green]分表导出完成:[/green] 共导出 {total_exported} 条数据")
        else:
            # 普通导出
            if not output_file:
                if config_manager.get("only_export_words", False):
                    # 只导出词表
                    words_export_name = config_manager.get("words_export_name", "vmtool_words")
                    output_file = os.path.join(export_path, f"{words_export_name}.{format}")
                else:
                    # 导出所有数据
                    default_export_name = config_manager.get("default_export_name", "vmtool_export")
                    output_file = os.path.join(export_path, f"{default_export_name}.{format}")
            
            if config_manager.get("only_export_words", False):
                # 只导出词表
                result = dict_service.export_data(output_file, format, table="words")
                
                # 检查是否需要自动导出到 Rime 目录
                if config_manager.get("auto_export_ibus_rime", False):
                    ibus_rime_path = os.path.expanduser("~/.config/ibus/rime")
                    if os.path.exists(ibus_rime_path):
                        # 复制文件到 ibus/rime 目录
                        try:
                            import shutil
                            shutil.copy(output_file, ibus_rime_path)
                            console.print(f"[green]自动导出到 ibus/rime 目录成功[/green]")
                        except Exception as e:
                            console.print(f"[yellow]自动导出到 ibus/rime 目录失败:[/yellow] {e}")
                
                if config_manager.get("auto_export_fcitx5_rime", False):
                    fcitx5_rime_path = os.path.expanduser("~/.local/share/fcitx5/rime")
                    if os.path.exists(fcitx5_rime_path):
                        # 复制文件到 fcitx5/rime 目录
                        try:
                            import shutil
                            shutil.copy(output_file, fcitx5_rime_path)
                            console.print(f"[green]自动导出到 fcitx5/rime 目录成功[/green]")
                        except Exception as e:
                            console.print(f"[yellow]自动导出到 fcitx5/rime 目录失败:[/yellow] {e}")
            else:
                # 导出所有数据
                result = dict_service.export_data(output_file, format)
                
                # 检查是否需要自动导出到 Rime 目录
                if config_manager.get("auto_export_ibus_rime", False):
                    ibus_rime_path = os.path.expanduser("~/.config/ibus/rime")
                    if os.path.exists(ibus_rime_path):
                        # 复制文件到 ibus/rime 目录
                        try:
                            import shutil
                            shutil.copy(output_file, ibus_rime_path)
                            console.print(f"[green]自动导出到 ibus/rime 目录成功[/green]")
                        except Exception as e:
                            console.print(f"[yellow]自动导出到 ibus/rime 目录失败:[/yellow] {e}")
                
                if config_manager.get("auto_export_fcitx5_rime", False):
                    fcitx5_rime_path = os.path.expanduser("~/.local/share/fcitx5/rime")
                    if os.path.exists(fcitx5_rime_path):
                        # 复制文件到 fcitx5/rime 目录
                        try:
                            import shutil
                            shutil.copy(output_file, fcitx5_rime_path)
                            console.print(f"[green]自动导出到 fcitx5/rime 目录成功[/green]")
                        except Exception as e:
                            console.print(f"[yellow]自动导出到 fcitx5/rime 目录失败:[/yellow] {e}")
            
            console.print(f"[green]导出成功:[/green] 共导出 {result} 条数据")
    except Exception as e:
        console.print(f"[red]导出失败:[/red] {e}")





def show_typer_help():
    """显示与 --help 相同的帮助信息"""
    from click.testing import CliRunner
    from typer.main import get_command
    cmd = get_command(app)
    runner = CliRunner()
    result = runner.invoke(cmd, ['--help'])
    if result.output:
        console.print(result.output)
    if result.exception:
        raise result.exception








@app.command("gui")
def start_gui():
    """启动图形界面"""
    import sys as sys_module
    # 强制刷新输出
    if hasattr(sys_module.stdout, 'reconfigure'):
        sys_module.stdout.reconfigure(line_buffering=True)
    
    print("[CLI-GUI] ===== 开始启动 GUI =====", flush=True)
    try:
        console.print("[green]正在启动图形界面...[/green]")
        print("[CLI-GUI] [1/5] 导入 PyQt6 模块...", flush=True)
        # 导入并启动PyQt应用
        import sys as sys_module
        sys_module.path.insert(0, ".")
        from PyQt6.QtWidgets import QApplication
        print("[CLI-GUI] ✓ PyQt6 导入成功", flush=True)
        
        # 检查是否已经有 QApplication 实例
        print("[CLI-GUI] [2/5] 检查 QApplication 实例...", flush=True)
        qapp = QApplication.instance()
        if qapp is None:
            # 创建 QApplication 实例
            print("[CLI-GUI] 创建新的 QApplication 实例", flush=True)
            qapp = QApplication(sys_module.argv)
        else:
            print("[CLI-GUI] 使用已存在的 QApplication 实例", flush=True)
        print("[CLI-GUI] ✓ QApplication 就绪", flush=True)
        
        # 导入并创建主窗口
        print("[CLI-GUI] [3/5] 导入 VMTOOLPyQtApp...", flush=True)
        from ui.gui.pyqt_app import VMTOOLPyQtApp
        print("[CLI-GUI] ✓ VMTOOLPyQtApp 导入成功", flush=True)
        
        print("[CLI-GUI] [4/5] 创建主窗口...", flush=True)
        print("[CLI-GUI] 开始创建 VMTOOLPyQtApp 实例...", flush=True)
        window = VMTOOLPyQtApp()
        print(f"[CLI-GUI] ✓ 主窗口创建成功", flush=True)
        print(f"[CLI-GUI] 窗口对象: {window}", flush=True)
        print(f"[CLI-GUI] 窗口属性:", flush=True)
        print(f"[CLI-GUI]   - windowTitle: {window.windowTitle()}", flush=True)
        print(f"[CLI-GUI]   - size: {window.size().width()}x{window.size().height()}", flush=True)
        print(f"[CLI-GUI]   - centralWidget: {window.centralWidget()}", flush=True)
        print(f"[CLI-GUI]   - layout: {window.layout()}", flush=True)
        print(f"[CLI-GUI]   - isVisible: {window.isVisible()}", flush=True)
        print(f"[CLI-GUI]   - isMinimized: {window.isMinimized()}", flush=True)
        print(f"[CLI-GUI]   - isMaximized: {window.isMaximized()}", flush=True)
        
        print("[CLI-GUI] [5/5] 显示窗口...", flush=True)
        print("[CLI-GUI] 调用 window.show()...", flush=True)
        window.show()
        print(f"[CLI-GUI] ✓ window.show() 调用完成", flush=True)
        print(f"[CLI-GUI] 窗口状态检查:", flush=True)
        print(f"[CLI-GUI]   - isVisible: {window.isVisible()}", flush=True)
        print(f"[CLI-GUI]   - isActiveWindow: {window.isActiveWindow()}", flush=True)
        print(f"[CLI-GUI]   - isHidden: {window.isHidden()}", flush=True)
        print(f"[CLI-GUI]   - isMinimized: {window.isMinimized()}", flush=True)
        print(f"[CLI-GUI] 窗口大小: {window.size().width()}x{window.size().height()}", flush=True)
        print(f"[CLI-GUI] 窗口标题: {window.windowTitle()}", flush=True)
        
        # 启动事件循环
        print("[CLI-GUI] 准备启动 Qt 事件循环...", flush=True)
        
        # 在启动事件循环前，确保窗口可见
        print("[CLI-GUI] 最终窗口状态检查:", flush=True)
        print(f"[CLI-GUI]   - isVisible: {window.isVisible()}", flush=True)
        print(f"[CLI-GUI]   - isHidden: {window.isHidden()}", flush=True)
        print(f"[CLI-GUI]   - isMinimized: {window.isMinimized()}", flush=True)
        print(f"[CLI-GUI]   - geometry: {window.geometry()}", flush=True)
        print(f"[CLI-GUI]   - pos: {window.pos().x()},{window.pos().y()}", flush=True)
        
        # 如果窗口不可见，强制显示
        if not window.isVisible():
            print("[CLI-GUI] ⚠️  窗口不可见，强制调用 show()", flush=True)
            window.show()
            window.raise_()  # 提升到顶层
            window.activateWindow()  # 激活窗口
        
        # 确保窗口在屏幕可见区域内
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        win_geometry = window.geometry()
        print(f"[CLI-GUI] 屏幕大小: {screen.width()}x{screen.height()}", flush=True)
        print(f"[CLI-GUI] 窗口位置: ({win_geometry.x()}, {win_geometry.y()}), 大小: {win_geometry.width()}x{win_geometry.height()}", flush=True)
        
        # 如果窗口位置在屏幕外，移动到屏幕中心
        if (win_geometry.x() < -100 or win_geometry.y() < -100 or 
            win_geometry.x() > screen.width() + 100 or win_geometry.y() > screen.height() + 100):
            print("[CLI-GUI] ⚠️  窗口在屏幕外，移动到屏幕中心", flush=True)
            window.move(
                (screen.width() - win_geometry.width()) // 2,
                (screen.height() - win_geometry.height()) // 2
            )
        
        print("[CLI-GUI] 调用 app.exec()...", flush=True)
        print("[CLI-GUI] ===== GUI 启动完成，进入事件循环 =====", flush=True)
        
        # 这里会阻塞，直到应用退出
        exit_code = qapp.exec()
        print(f"[CLI-GUI] Qt 事件循环结束，退出码: {exit_code}", flush=True)
        sys_module.exit(exit_code)
    except Exception as e:
        print(f"[CLI-GUI] ✗ 启动图形界面失败: {e}")
        import traceback
        print(f"[CLI-GUI] 错误堆栈:")
        traceback.print_exc()
        console.print(f"[red]启动图形界面失败:[/red] {e}")
        console.print(f"[red]{traceback.format_exc()}[/red]")


if __name__ == "__main__":
    app()
