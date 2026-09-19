from PyQt6.QtCore import QThread, pyqtSignal

from .service_factory import dict_service_scope


class BaseBatchThread(QThread):
    """批量操作线程基类

    服务实例不再由外部注入：本类在 ``run()`` 内创建**线程私有**的 ``DictService``
    （见 ``service_factory``），退出时释放；``process_item`` 通过参数拿到该实例。
    构造签名里出现服务实例参数会被 ``tests/unit/test_gui_thread_conventions.py``
    静态判失败。
    """

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, items: list, is_character: bool = False):
        super().__init__()
        self.items = items
        self.is_character = is_character
        self.total = len(items)
        self.added = 0
        self.failed = 0

    def run(self):
        """执行批量操作（服务实例在本线程内创建与释放）"""
        try:
            with dict_service_scope() as dict_service:
                last_progress = -1
                for i, item in enumerate(self.items):
                    try:
                        self.process_item(item, dict_service)
                        self.added += 1
                    except Exception as e:
                        self.failed += 1
                        current_progress = int((i + 1) / self.total * 100)
                        if current_progress != last_progress:
                            self.progress.emit(
                                current_progress, f"处理失败: {item} - {str(e)}"
                            )
                            last_progress = current_progress
                    # 只在进度变化时发射信号，避免过多信号导致GUI卡顿
                    current_progress = int((i + 1) / self.total * 100)
                    if current_progress != last_progress:
                        self.progress.emit(
                            current_progress, f"处理中: {item} ({i + 1}/{self.total})"
                        )
                        last_progress = current_progress
                self.finished.emit(
                    {"total": self.total, "added": self.added, "failed": self.failed}
                )
        except Exception as e:
            self.error.emit(str(e))

    def process_item(self, item, dict_service):
        """处理单个项，子类必须重写

        ``dict_service`` 是本线程私有的实例，由 ``run()`` 传入。子类不得把它存到
        ``self`` 上供后续复用（那会重新变成跨线程/跨任务共享同一个会话）。
        """
        raise NotImplementedError
