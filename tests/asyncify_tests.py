import unittest
from tests.testdata import TestClassAsyncify, TestClass

class AsyncifyTests(unittest.IsolatedAsyncioTestCase):
    
    async def test_asyncify_instancemethods_returnscoro(self):
       expected = TestClassAsyncify.sync_method.__name__
       async_obj = TestClassAsyncify(100)
       async_resp = await async_obj.sync_method()
       self.assertEqual(expected, async_resp)

    def test_asyncify_staticmethods_doesnotasyncify(self):
       expected = TestClassAsyncify.sync_static_method.__name__
       async_obj = TestClassAsyncify(100)
       async_resp = async_obj.sync_static_method()
       self.assertEqual(expected, async_resp)

    def test_asyncify_classmethods_doesnotasyncify(self):
       expected = f"{TestClassAsyncify.__name__}.{TestClassAsyncify.sync_class_method.__name__}"
       async_obj = TestClassAsyncify(100)
       async_resp = async_obj.sync_class_method()
       self.assertEqual(expected, async_resp)

    async def test_asyncify_existing_asyncmethods_runssuccessfully(self):
       expected = TestClassAsyncify.async_method.__name__
       async_obj = TestClassAsyncify(100)
       async_resp = await async_obj.async_method()
       self.assertEqual(expected, async_resp)

if __name__ == "__main__":
    unittest.main()