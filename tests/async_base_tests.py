import unittest
from tests.testdata import TestClassAsyncWrapper

class AsyncBaseTests(unittest.IsolatedAsyncioTestCase):
    
    async def test_asyncbaseclass_instancemethods_returnscoro(self):
       expected = TestClassAsyncWrapper.sync_method.__name__
       async_obj = TestClassAsyncWrapper(100)
       async_resp = await async_obj.sync_method()
       self.assertEqual(expected, async_resp)
    
    async def test_asyncbaseclass_staticmethods_returnscoro(self):
       expected = TestClassAsyncWrapper.sync_static_method.__name__
       async_obj = TestClassAsyncWrapper(100)
       async_resp = await async_obj.sync_static_method()
       self.assertEqual(expected, async_resp)

    async def test_asyncbaseclass_classmethods_doesnotasyncify(self):
       expected = f"{TestClassAsyncWrapper.__name__}.{TestClassAsyncWrapper.sync_class_method.__name__}"
       async_obj = TestClassAsyncWrapper(100)
       async_resp = await async_obj.sync_class_method()
       self.assertEqual(expected, async_resp)

    async def test_asyncify_asyncmethods_nochange(self):
       expected = TestClassAsyncWrapper.async_method.__name__
       async_obj = TestClassAsyncWrapper(100)
       async_resp = await async_obj.async_method()
       self.assertEqual(expected, async_resp)


if __name__ == "__main__":
    unittest.main()