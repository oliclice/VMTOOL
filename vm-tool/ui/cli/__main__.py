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

# 初始化服务
dict_service = DictService()
weight_calc = WeightCalculator()
filter_service = FilterService()
stats_service = StatsService()
compatibility = CompatibilityLayer()


@app.command("add")
def add_word(word: str, code: Optional[str] = None, weight: float = 1.0):
    """添加词条"""
    try:
        result = dict_service.add_word(word, code, weight)
        console.print(f"[green]添加成功:[/green] {result}")
    except Exception as e:
        console.print(f"[red]添加失败:[/red] {e}")


@app.command("add-batch")
def add_batch(words: List[str]):
    """批量添加词条"""
    try:
        word_data = []
        for word in words:
            # 简单处理，实际应用中可能需要更复杂的解析
            word_data.append({"word": word, "code": None, "weight": 1.0})
        
        result = dict_service.add_words(word_data)
        console.print(f"[green]批量添加完成:[/green] 添加了 {result['added']} 条，跳过了 {result['existing']} 条")
    except Exception as e:
        console.print(f"[red]批量添加失败:[/red] {e}")


@app.command("delete")
def delete_word(word: str):
    """删除词条"""
    try:
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


@app.command("update-weight")
def update_weight(word: str, increment: float = 0.1):
    """更新词条权重"""
    try:
        result = weight_calc.update_word_weight(word, increment)
        console.print(f"[green]更新权重成功:[/green] {result}")
    except Exception as e:
        console.print(f"[red]更新权重失败:[/red] {e}")


@app.command("set-weight")
def set_weight(word: str, weight: float):
    """直接设置词条权重"""
    try:
        result = weight_calc.set_weight_directly(word, weight)
        console.print(f"[green]设置权重成功:[/green] {result}")
    except Exception as e:
        console.print(f"[red]设置权重失败:[/red] {e}")


@app.command("replace-code")
def replace_code(word: str, new_code: str):
    """替换词条编码"""
    try:
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
        # 设置编码生成配置
        config = {
            'rule': rule,
            'separator': separator,
            'max_length': max_length
        }
        dict_service.code_generator.set_config(config)
        
        # 批量计算编码
        result = dict_service.calculate_all_codes()
        
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
def import_data(file_path: str, format: str = "txt"):
    """导入数据"""
    try:
        if format == "txt":
            result = filter_service.import_from_txt(file_path)
        elif format == "csv":
            result = filter_service.import_from_csv(file_path)
        elif format == "json":
            result = filter_service.import_from_json(file_path)
        else:
            console.print(f"[red]不支持的格式:[/red] {format}")
            return
        
        console.print(f"[green]导入成功:[/green] 添加了 {result['added']} 条，跳过了 {result['existing']} 条")
    except Exception as e:
        console.print(f"[red]导入失败:[/red] {e}")


@app.command("export")
def export_data(output_file: str, format: str = "txt"):
    """导出数据"""
    try:
        if format == "txt":
            count = filter_service.export_to_txt(output_file)
        elif format == "csv":
            count = filter_service.export_to_csv(output_file)
        elif format == "json":
            count = filter_service.export_to_json(output_file)
        else:
            console.print(f"[red]不支持的格式:[/red] {format}")
            return
        
        console.print(f"[green]导出成功:[/green] 共导出 {count} 条数据")
    except Exception as e:
        console.print(f"[red]导出失败:[/red] {e}")


@app.command("migrate")
def migrate_data(old_file: Optional[str] = None):
    """迁移旧数据"""
    try:
        from app.dal.migration import full_migration
        result = full_migration()
        console.print("[green]数据迁移完成[/green]")
        console.print(f"数据迁移: {result['data_migration']}")
        console.print(f"配置迁移: {result['config_migration']}")
        console.print(f"数据验证: {result['validation']}")
        console.print(f"数据修复: {result['fix']}")
    except Exception as e:
        console.print(f"[red]迁移失败:[/red] {e}")


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





@app.command("old")
def old_interface(args: List[str]):
    """旧版本接口兼容"""
    compatibility.handle_old_command_line(args)


@app.command("gui")
def start_gui():
    """启动图形界面"""
    try:
        console.print("[green]正在启动图形界面...[/green]")
        # 导入并启动PyQt应用
        import sys
        sys.path.insert(0, ".")
        from ui.gui.pyqt_app import VMTOOLPyQtApp
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        window = VMTOOLPyQtApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        console.print(f"[red]启动图形界面失败:[/red] {e}")


if __name__ == "__main__":
    app()
