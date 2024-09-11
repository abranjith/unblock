import unittest
from tests.testdata import TestClassAsyncPPWrapper

class AsyncBaseTests(unittest.IsolatedAsyncioTestCase):
    
    async def test_asyncbaseclass_instancemethods_returnscoro(self):
       expected = TestClassAsyncPPWrapper.sync_method.__name__
       async_obj = TestClassAsyncPPWrapper(100)
       async_resp = await async_obj.sync_method()
       self.assertEqual(expected, async_resp)
    
    async def test_asyncbaseclass_staticmethods_returnscoro(self):
       expected = TestClassAsyncPPWrapper.sync_static_method.__name__
       async_obj = TestClassAsyncPPWrapper(100)
       async_resp = await async_obj.sync_static_method()
       self.assertEqual(expected, async_resp)

    async def test_asyncbaseclass_classmethods_doesnotasyncify(self):
       expected = f"{TestClassAsyncPPWrapper.__name__}.{TestClassAsyncPPWrapper.sync_class_method.__name__}"
       async_obj = TestClassAsyncPPWrapper(100)
       async_resp = await async_obj.sync_class_method()
       self.assertEqual(expected, async_resp)

    async def test_asyncify_asyncmethods_nochange(self):
       expected = TestClassAsyncPPWrapper.async_method.__name__
       async_obj = TestClassAsyncPPWrapper(100)
       async_resp = await async_obj.async_method()
       self.assertEqual(expected, async_resp)


if __name__ == "__main__":
    unittest.main()