"""
unblock.common - Shared Utilities

This module provides common utilities and building blocks used across the 'unblock' library.
It primarily focuses on:
1.  Registry: A centralized mechanism for managing and accessing the asyncio event loop,
    ThreadPoolExecutor, and ProcessPoolExecutor instances. This allows users to configure
    custom loops or executors if needed, while providing sensible defaults.
2.  UnblockException: A custom base exception class for library-specific errors.
"""

import asyncio
import warnings # Added for issuing warnings
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Union, Optional


def set_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """
    Sets a custom asyncio event loop to be used by the unblock library.

    Args:
        loop: The asyncio.AbstractEventLoop instance to register.
    """
    Registry.register_event_loop(loop)


def set_threadpool_executor(executor: ThreadPoolExecutor) -> None:
    """
    Sets a custom ThreadPoolExecutor to be used by the unblock library
    for thread-based asynchronous operations.

    Args:
        executor: The ThreadPoolExecutor instance to register.
    """
    Registry.register_threadpool_executor(executor)


def set_processpool_executor(executor: ProcessPoolExecutor) -> None:
    """
    Sets a custom ProcessPoolExecutor to be used by the unblock library
    for process-based asynchronous operations.

    Args:
        executor: The ProcessPoolExecutor instance to register.
    """
    Registry.register_processpool_executor(executor)


_THREAD_NAME_PREFIX = "unblock.asyncio"  # Default thread name prefix for the default ThreadPoolExecutor


class Registry:
    """
    Manages and provides access to global asyncio event loop and executor instances.

    This class allows users to optionally set custom event loops or executors.
    If no custom instances are provided, it falls back to default configurations
    (e.g., the current running event loop, or newly created executors), issuing
    a UserWarning in such cases.
    """

    _loop: Optional[asyncio.AbstractEventLoop] = None
    _thread_executor: Optional[ThreadPoolExecutor] = None
    _process_executor: Optional[ProcessPoolExecutor] = None

    @staticmethod
    def register_event_loop(loop: asyncio.AbstractEventLoop) -> None:
        """
        Registers a specific asyncio event loop for the library to use.

        Args:
            loop: The event loop instance.
        """
        Registry._loop = loop

    @staticmethod
    def get_event_loop() -> asyncio.AbstractEventLoop:
        """
        Retrieves the registered event loop, or the default event loop if none is registered.

        If no event loop is registered, it issues a UserWarning and falls back to
        `asyncio.get_running_loop()`. This method will raise a RuntimeError if called
        when no loop is running and no loop has been explicitly registered.

        Returns:
            The active asyncio.AbstractEventLoop.
        """
        if Registry._loop is not None:
            return Registry._loop
        
        warnings.warn(
            "No event loop registered via unblock.set_event_loop(). "
            "Falling back to asyncio.get_running_loop().",
            UserWarning,
            stacklevel=2
        )
        return Registry._get_default_event_loop()

    @staticmethod
    def register_threadpool_executor(executor: ThreadPoolExecutor) -> None:
        """
        Registers a specific ThreadPoolExecutor instance.

        Args:
            executor: The ThreadPoolExecutor instance.
        """
        Registry._ensure_executor(executor)
        Registry._thread_executor = executor

    @staticmethod
    def get_threadpool_executor() -> ThreadPoolExecutor:
        """
        Retrieves the registered ThreadPoolExecutor, or creates a default one if none is registered.

        If no executor is registered, it issues a UserWarning and creates a default
        ThreadPoolExecutor with a specific thread name prefix.

        Returns:
            The active ThreadPoolExecutor.
        """
        if Registry._thread_executor is None:
            warnings.warn(
                "No ThreadPoolExecutor registered. Using default unblock ThreadPoolExecutor. "
                "Call unblock.set_threadpool_executor() to customize.",
                UserWarning,
                stacklevel=2
            )
            # Create a default ThreadPoolExecutor if none has been registered.
            Registry._thread_executor = ThreadPoolExecutor(
                thread_name_prefix=_THREAD_NAME_PREFIX
            )
        return Registry._thread_executor

    @staticmethod
    def register_processpool_executor(executor: ProcessPoolExecutor) -> None:
        """
        Registers a specific ProcessPoolExecutor instance.

        Args:
            executor: The ProcessPoolExecutor instance.
        """
        Registry._ensure_executor(executor, process_pool=True)
        Registry._process_executor = executor

    @staticmethod
    def get_processpool_executor() -> ProcessPoolExecutor:
        """
        Retrieves the registered ProcessPoolExecutor, or creates a default one if none is registered.

        If no executor is registered, it issues a UserWarning and creates a default
        ProcessPoolExecutor.

        Returns:
            The active ProcessPoolExecutor.
        """
        if Registry._process_executor is None:
            warnings.warn(
                "No ProcessPoolExecutor registered. Using default unblock ProcessPoolExecutor. "
                "Call unblock.set_processpool_executor() to customize.",
                UserWarning,
                stacklevel=2
            )
            # Create a default ProcessPoolExecutor if none has been registered.
            Registry._process_executor = ProcessPoolExecutor()
        return Registry._process_executor

    @staticmethod
    def is_event_loop_running() -> bool:
        """
        Checks if an asyncio event loop is currently running in the current thread.

        Returns:
            True if an event loop is running, False otherwise.
        """
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:  # No running event loop
            return False

    @staticmethod
    def _ensure_executor(
        executor: Union[ProcessPoolExecutor, ThreadPoolExecutor],
        process_pool: bool = False,
    ) -> None:
        """
        Validates the type of the provided executor.

        Args:
            executor: The executor instance to check.
            process_pool: If True, expects a ProcessPoolExecutor; otherwise, expects a ThreadPoolExecutor.

        Raises:
            ValueError: If the executor is not of the expected type.
        """
        if process_pool:
            if not isinstance(executor, ProcessPoolExecutor):
                raise ValueError(
                    f"Executor {executor} must be of type concurrent.futures.ProcessPoolExecutor"
                )
        else:
            if not isinstance(executor, ThreadPoolExecutor):
                raise ValueError(
                    f"Executor {executor} must be of type concurrent.futures.ThreadPoolExecutor"
                )

    @staticmethod
    def _get_default_event_loop() -> asyncio.AbstractEventLoop:
        """
        Internal helper to get the current running event loop.

        This is used as a fallback if no loop is explicitly registered via `register_event_loop`.
        It relies on `asyncio.get_running_loop()`, which is generally the desired behavior
        to integrate with the currently active asyncio environment.

        Returns:
            The current running asyncio.AbstractEventLoop.

        Raises:
            RuntimeError: If there is no running event loop in the current OS thread.
        """
        # This will raise a RuntimeError if no loop is running, which is the expected
        # behavior if the user hasn't set one and isn't in an asyncio context.
        return asyncio.get_running_loop()


class UnblockException(Exception):
    """
    Base exception class for errors raised by the 'unblock' library.

    This allows users to catch all library-specific exceptions by catching
    this single type.
    """
    pass
