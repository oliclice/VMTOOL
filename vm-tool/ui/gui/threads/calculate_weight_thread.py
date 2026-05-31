from PyQt6.QtCore import QThread, pyqtSignal


class CalculateWeightThread(QThread):
    """批量计算权重线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, weight_calc):
        super().__init__()
        self.weight_calc = weight_calc

    def run(self):
        try:
            def progress_callback(progress, message):
                self.progress.emit(progress, message)

            result = self.weight_calc.recalculate_all_weights(progress_callback)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
