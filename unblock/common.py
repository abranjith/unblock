import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

THREAD_NAME_PREFIX = "unblock.asyncio"


def set_event_loop(loop):
    Registry.register_event_loop(loop)


def set_threadpool_executor(executor):
    Registry.register_threadpool_executor(executor)


def set_processpool_executor(executor):
    Registry.register_processpool_executor(executor)


class Registry:
    _loop = None
    _thread_executor = None
    _process_executor = None

    @staticmethod
    def register_event_loop(loop):
        Registry._loop = loop

    @staticmethod
    def get_event_loop():
        return Registry._loop or Registry._get_default_event_loop()

    @staticmethod
    def register_threadpool_executor(executor):
        Registry._ensure_executor(executor)
        Registry._thread_executor = executor

    @staticmethod
    def get_threadpool_executor():
        Registry._thread_executor = Registry._thread_executor or ThreadPoolExecutor(
            thread_name_prefix=THREAD_NAME_PREFIX
        )
        return Registry._thread_executor

    @staticmethod
    def register_processpool_executor(executor):
        Registry._ensure_executor(executor, process_pool=True)
        Registry._process_executor = executor

    @staticmethod
    def get_processpool_executor():
        Registry._process_executor = Registry._process_executor or ProcessPoolExecutor()
        return Registry._process_executor

    @staticmethod
    def is_event_loop_running():
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False

    @staticmethod
    def _ensure_executor(executor, process_pool=False):
        if process_pool:
            if not isinstance(executor, ProcessPoolExecutor):
                raise ValueError(
                    f"{executor} needs to be of type concurrent.futures.ProcessPoolExecutor"
                )
        else:
            if not isinstance(executor, ThreadPoolExecutor):
                raise ValueError(
                    f"{executor} needs to be of type concurrent.futures.ThreadPoolExecutor"
                )

    @staticmethod
    def _get_default_event_loop():
        return asyncio.get_running_loop()
