#!/usr/bin/env python3
"""
码表处理工具 - 主程序
支持命令行参数和交互式菜单
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from dict_manager import DictManager
from weight_calculator import WeightCalculator
from file_ops import FileReader, FileWriter
from timer import Timer
from menu import Menu, RichMenu


class DictTool:
    """码表处理工具主类"""
    
    def __init__(self):
        self.config = Config()
        self.dict_mgr = DictManager(self.config)
        self.weight_calc = WeightCalculator()
        self.writer = FileWriter()
        self.menu = Menu(self.dict_mgr, self.weight_calc, self.writer)
        self.rich_menu = RichMenu(self.dict_mgr, self.weight_calc, self.writer)
    
    def run(self, args=None):
        """运行工具"""
        parsed = self._parse_args(args)
        
        if self._handle_args(parsed):
            return
        
        # 没有命令行参数，启动交互菜单
        try:
            self.rich_menu.show()
        except Exception:
            self.menu.main_loop()
    
    def _parse_args(self, args=None) -> argparse.Namespace:
        """解析命令行参数"""
        parser = argparse.ArgumentParser(description="码表处理工具")
        
        # 添加参数
        parser.add_argument('-a', '--add', nargs='*', help='添加新词')
        parser.add_argument('-d', '--delete', nargs='*', help='删除词')
        parser.add_argument('-q', '--query', help='查词或查编码')
        parser.add_argument('-u', '--update-weight', nargs='*', help='更新词权重')
        parser.add_argument('-U', '--set-weight', nargs=2, metavar=('词', '值'), help='直接设置词权重')
        parser.add_argument('-r', '--replace', nargs=2, metavar=('词', '新编码'), help='替换编码')
        parser.add_argument('-H', '--high-key', nargs=2, metavar=('最小长度', '出现次数'), help='高频统计')
        parser.add_argument('-C', '--clear', help='清理备份文件(y确认)')
        parser.add_argument('-c', '--choices', nargs='*', help='执行指定功能')
        
        return parser.parse_args(args)
    
    def _handle_args(self, args: argparse.Namespace) -> bool:
        """处理命令行参数，返回是否应该退出"""
        if args.add:
            return self._add_words(args.add)
        
        if args.delete:
            return self._delete_words(args.delete)
        
        if args.query:
            self.dict_mgr.query(args.query)
            return True
        
        if args.update_weight:
            return self._update_weights(args.update_weight)
        
        if args.set_weight:
            return self._set_weight(args.set_weight)
        
        if args.replace:
            self.dict_mgr.replace_key(args.replace[0], args.replace[1])
            self._write_files()
            return True
        
        if args.high_key:
            Timer.time_execution('高频统计', 
                                 lambda: self.dict_mgr.count_high_keys(int(args.high_key[0]), int(args.high_key[1])))
            return True
        
        if args.clear:
            self.dict_mgr.clear_backups(args.clear)
            return True
        
        if args.choices:
            for c in args.choices:
                self.menu._run_function(int(c))
            return True
        
        return False
    
    def _add_words(self, words: list) -> bool:
        """添加新词"""
        new_data = {}
        for word in words:
            if word in self.dict_mgr.data:
                print(f'{word} 已存在: {self.dict_mgr.data[word]}')
                continue
            
            new_key = self.dict_mgr._generate_key(word)
            new_data[word] = {"key": new_key, "weight": 1, "exsit": True}
            
            if new_key == '?':
                print(f'错误: 无法为"{word}"生成编码')
            else:
                print(f'{word}: {new_data[word]}')
        
        if new_data:
            self.dict_mgr.data.update(new_data)
            self._write_files(new_data, append=True)
        
        return True
    
    def _delete_words(self, words: list) -> bool:
        """删除词"""
        self.dict_mgr.remove_words(words)
        self._write_files()
        return True
    
    def _update_weights(self, words: list) -> bool:
        """更新权重"""
        for word in words:
            if word in self.dict_mgr.data:
                self.weight_calc.update_word_weight(self.dict_mgr.data, word)
            else:
                print(f'{word} 不在数据中')
        self._write_files()
        return True
    
    def _set_weight(self, args: list) -> bool:
        """直接设置权重"""
        word, value = args
        if word in self.dict_mgr.data:
            self.weight_calc.set_weight_directly(self.dict_mgr.data, word, value)
        else:
            print(f'词 "{word}" 不在数据中')
        self._write_files()
        return True
    
    def _write_files(self, new_data=None, append=False):
        """写入文件并复制"""
        startwith_path = self.config.base_dir + '/startwith.txt'
        
        if new_data and append:
            self.writer.append_dict(new_data, self.config.output_file)
        else:
            self.writer.write_dict(self.dict_mgr.data, self.config.output_file, startwith_path)
        
        self.writer.copy_file(self.config.output_file, self.config.base_dir + '/dicts', 'main.txt')
        self.writer.copy_file(self.config.output_file, self.config.target_rime_path, 'flypy_user.txt')


def main():
    """主函数"""
    try:
        DictTool().run()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序运行出错: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
