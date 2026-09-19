from PyQt6.QtCore import QThread, pyqtSignal

from .service_factory import weight_calculator_scope


class CalculateWeightThread(QThread):
    """批量计算权重线程

    不再接受外部注入的 ``WeightCalculator``：服务与其会话在 ``run()`` 内创建于本
    线程，``with`` 退出时关闭。

    信号声明与 ``CalculateThread`` / HEAD 保持一致 —— 调用方（``pyqt_app`` 的
    「重新计算权重」入口）会连接 progress / finished / error 三个信号，缺一即在
    运行时 ``AttributeError``。``tests/unit/test_gui_thread_conventions.py`` 的第 5 条
    AST 规则会把这类缺失静态判失败。
    """

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:

            def progress_callback(progress, message):
                self.progress.emit(progress, message)

            with weight_calculator_scope() as weight_calc:
                result = weight_calc.recalculate_all_weights(progress_callback)

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
