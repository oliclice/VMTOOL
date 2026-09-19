from PyQt6.QtCore import QThread, pyqtSignal

from .service_factory import dict_service_scope


class CalculateThread(QThread):
    """批量计算编码线程

    不再接受外部注入的 ``DictService``：服务实例在 ``run()`` 内创建于本线程，
    ``with`` 退出时释放（防复发约定见 ``service_factory``）。
    """

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            self.progress.emit(0, "准备计算编码...")

            # 定义进度回调函数
            def progress_callback(progress, message):
                self.progress.emit(progress, message)

            # 服务实例由本线程创建并负责释放
            with dict_service_scope() as dict_service:
                result = dict_service.calculate_all_codes(progress_callback)

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
