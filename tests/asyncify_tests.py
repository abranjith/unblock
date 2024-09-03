import unittest
import inspect
from tests.testdata import TestClassAsyncify, TestClass

class AsyncifyTests(unittest.TestCase):
    
    def test_asyncifyinstancemethods_returns_coro(self):
       sync_obj  = TestClass(100)
       sync_resp = sync_obj.sync_method()
       self.assertEqual(sync_obj.sync_method.__name__, sync_resp)
       async_obj = TestClassAsyncify(100)
       async_resp = async_obj.sync_method()
       print(inspect.iscoroutinefunction(async_resp))

if __name__ == "__main__":
    unittest.main()