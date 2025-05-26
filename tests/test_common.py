import unittest
import warnings
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from unblock.common import Registry, set_event_loop, set_threadpool_executor, set_processpool_executor

class TestRegistryWarnings(unittest.TestCase):

    def setUp(self):
        # Save the original state of Registry attributes
        self._original_loop = Registry._loop
        self._original_thread_executor = Registry._thread_executor
        self._original_process_executor = Registry._process_executor

        # Reset Registry attributes to None before each test
        Registry._loop = None
        Registry._thread_executor = None
        Registry._process_executor = None

    def tearDown(self):
        # Restore the original state of Registry attributes after each test
        Registry._loop = self._original_loop
        Registry._thread_executor = self._original_thread_executor
        Registry._process_executor = self._original_process_executor

    def test_get_threadpool_executor_issues_warning_when_not_set(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")  # Cause all warnings to always be triggered.
            executor = Registry.get_threadpool_executor()
            
            self.assertIsNotNone(executor)
            self.assertIsInstance(executor, ThreadPoolExecutor)
            # Ensure the default executor is cleaned up if it's started by the test
            if hasattr(executor, '_shutdown') and not executor._shutdown:
                 executor.shutdown(wait=True)

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, UserWarning))
            self.assertIn("No ThreadPoolExecutor registered.", str(w[-1].message))

    def test_get_threadpool_executor_no_warning_when_set(self):
        my_executor = ThreadPoolExecutor(max_workers=1)
        set_threadpool_executor(my_executor) # This sets Registry._thread_executor
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            executor = Registry.get_threadpool_executor()
            
            self.assertIs(executor, my_executor)  # Should be the one we set
            self.assertEqual(len(w), 0)  # No warning
        
        # Clean up the executor we created for the test
        my_executor.shutdown(wait=True)

    def test_get_processpool_executor_issues_warning_when_not_set(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            executor = Registry.get_processpool_executor()
            
            self.assertIsNotNone(executor)
            self.assertIsInstance(executor, ProcessPoolExecutor)
            if hasattr(executor, '_shutdown') and not executor._shutdown: # Python 3.9+
                executor.shutdown(wait=True, cancel_futures=False) # cancel_futures=False for compatibility
            elif hasattr(executor, 'shutdown'): # older versions
                executor.shutdown(wait=True)


            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, UserWarning))
            self.assertIn("No ProcessPoolExecutor registered.", str(w[-1].message))

    def test_get_processpool_executor_no_warning_when_set(self):
        my_executor = ProcessPoolExecutor(max_workers=1)
        set_processpool_executor(my_executor) # This sets Registry._process_executor
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            executor = Registry.get_processpool_executor()
            
            self.assertIs(executor, my_executor)
            self.assertEqual(len(w), 0)
        
        my_executor.shutdown(wait=True)

    def test_get_event_loop_issues_warning_when_not_set(self):
        # This test needs an event loop to be running for _get_default_event_loop() to work
        # if Registry._loop is None.
        async def run_test():
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                loop = Registry.get_event_loop()
                
                self.assertIsNotNone(loop)
                self.assertIsInstance(loop, asyncio.AbstractEventLoop)
                self.assertEqual(len(w), 1)
                self.assertTrue(issubclass(w[-1].category, UserWarning))
                self.assertIn("No event loop registered via unblock.set_event_loop(). Falling back to asyncio.get_running_loop().", str(w[-1].message))

        # If an event loop is already running (e.g. from test runner), use it.
        # Otherwise, start a new one for this test.
        try:
            asyncio.get_running_loop()
            asyncio.run(run_test())
        except RuntimeError: # No current event loop
             asyncio.run(run_test())


    def test_get_event_loop_no_warning_when_set(self):
        # Create a new event loop for testing purposes
        # Note: This loop is not set as the current running loop for asyncio,
        # it's just an object we pass to the Registry.
        my_loop = asyncio.new_event_loop()
        self.addCleanup(my_loop.close) # Ensure the loop is closed after the test

        set_event_loop(my_loop) # This sets Registry._loop
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            loop = Registry.get_event_loop()
            
            self.assertIs(loop, my_loop)
            self.assertEqual(len(w), 0)

if __name__ == '__main__':
    unittest.main()
