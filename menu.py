#!/usr/bin/env python3
"""交互式菜单模块"""

import re
from datetime import datetime
from dict_manager import DictManager
from weight_calculator import WeightCalculator
from file_ops import FileWriter
from timer import Timer


class BaseMenu:
    """菜单基类"""

    def __init__(
        self,
        dict_manager: DictManager,
        weight_calc: WeightCalculator,
        file_writer: FileWriter,
    ):
        self.dict_mgr = dict_manager
        self.weight_calc = weight_calc
        self.writer = file_writer

    def _run_function(self, func_id: int):
        """执行功能"""
        cfg = self.dict_mgr.config.FUNCTIONS
        if func_id >= len(cfg):
            print(f"无效选择: {func_id}")
            return

        print(f"\n执行: {cfg[func_id].name}")

        if func_id == 1:
            Timer.time_execution("过滤词条", self.dict_mgr.filter)
        elif func_id == 2:
            Timer.time_execution(
                "计算权重", lambda: self.weight_calc.calculate_all(self.dict_mgr.data)
            )
        elif func_id == 3:
            Timer.time_execution("码表补充", self.dict_mgr.scan_and_add)
        elif func_id == 4:
            Timer.time_execution("写入码表", lambda: self._write_and_copy())
        elif func_id == 5:
            Timer.time_execution("刷新字表", self.dict_mgr.refresh_words_dict)
        elif func_id == 6:
            errors, words = self.dict_mgr.correct_codes()
            if errors:
                print(f"补码失败: {words}")
        elif func_id == 7:
            Timer.time_execution(
                "高频统计", lambda: self.dict_mgr.count_high_keys(4, 10)
            )
        elif func_id == 0:
            exit()

    def _write_and_copy(self):
        """写入文件并复制"""
        startwith_path = self.dict_mgr.config.base_dir + "/startwith.txt"
        self.writer.write_dict(
            self.dict_mgr.data,
            self.dict_mgr.config.output_file,
            startwith_path
        )
        self.writer.copy_file(
            self.dict_mgr.config.output_file,
            self.dict_mgr.config.base_dir + "/dicts",
            "main.txt",
        )
        self.writer.copy_file(
            self.dict_mgr.config.output_file,
            self.dict_mgr.config.target_rime_path,
            "flypy_user.txt",
        )


class Menu(BaseMenu):
    """交互式菜单"""

    def show_menu(self):
        """显示菜单"""
        print("\n" + "=" * 50)
        print("码表处理工具")
        print("=" * 50)
        for func in self.dict_mgr.config.FUNCTIONS:
            print(f"{func.id}. {func.name} - {func.desc}")
        print("=" * 50)

    def main_loop(self):
        """主循环"""
        while True:
            try:
                self.show_menu()
                choices = input("请输入选择 (多个用空格分隔, 退出): ").strip()

                if choices.lower() in ["q", "exit"]:
                    break

                start = datetime.now()
                self._execute(choices)
                print(f"\n总计耗时: {(datetime.now() - start).total_seconds():.3f}秒\n")

            except KeyboardInterrupt:
                print("\n程序被用户中断")
                break
            except Exception as e:
                print(f"发生错误: {e}")

    def _execute(self, choices: str):
        """执行选择"""
        for choice in re.split(r"[,\s]+", choices):
            if not choice or not choice.isdigit():
                continue

            self._run_function(int(choice))


class RichMenu(BaseMenu):
    """Rich美化菜单"""

    def show(self):
        """显示Rich菜单"""
        try:
            from rich.console import Console
            from rich.prompt import Prompt, Confirm
            from rich.panel import Panel
            from rich.table import Table
            from rich import box

            console = Console()

            def show_menu():
                console.clear()
                console.print(
                    Panel.fit(
                        "[bold cyan]📊 码表处理工具[/bold cyan]\n[dim]TUI交互界面[/dim]",
                        border_style="cyan",
                        padding=(1, 2),
                    )
                )

                table = Table(
                    box=box.ROUNDED, show_header=True, header_style="bold magenta"
                )
                table.add_column("编号", style="cyan", width=6)
                table.add_column("功能", style="green", width=12)
                table.add_column("描述", style="white")

                for func in self.dict_mgr.config.FUNCTIONS:
                    table.add_row(str(func.id), func.name, func.desc)

                console.print(table)
                self._show_status(console)

            def execute(input_str):
                if not input_str:
                    return True

                for choice in re.split(r"[,\s]+", input_str.strip()):
                    if not choice.isdigit():
                        continue

                    func_id = int(choice)
                    if func_id < len(self.dict_mgr.config.FUNCTIONS):
                        func = self.dict_mgr.config.FUNCTIONS[func_id]
                        console.print(f"[bold yellow]执行: {func.name}[/bold yellow]")

                        start = datetime.now()
                        self._run_function(func_id)
                        elapsed = (datetime.now() - start).total_seconds()
                        console.print(f"[green]✓ 完成! 耗时: {elapsed:.3f}秒[/green]")

                return True

            while True:
                show_menu()
                console.print("[bold cyan]操作说明:[/bold cyan]")
                console.print("• 输入多个数字用空格分隔批量执行")
                console.print("• 输入 'q' 退出")
                console.print("=" * 60)

                user_input = Prompt.ask("\n请输入选择", default="").strip()

                if user_input.lower() in ["q", "quit", "exit"]:
                    break
                else:
                    execute(user_input)
                    console.print()

                    if not Confirm.ask("继续操作？", default=True):
                        console.print("[cyan]再见！[/cyan]")
                        break

        except ImportError:
            print("未安装rich库，使用普通菜单")
            Menu(self.dict_mgr, self.weight_calc, self.writer).main_loop()
        except Exception as e:
            print(f"Rich菜单错误: {e}")
            Menu(self.dict_mgr, self.weight_calc, self.writer).main_loop()

    def _show_status(self, console):
        """显示状态"""
        try:
            from rich.text import Text

            status = Text()
            status.append("当前状态: ", style="bold")
            status.append(f"码表词数={len(self.dict_mgr.data)}, ", style="green")
            status.append(f"备份文件={self.dict_mgr.bak_counter}", style="red")
            console.print(status)
        except:
            pass
