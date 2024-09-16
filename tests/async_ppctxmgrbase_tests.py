import unittest
import asyncio
from tests.testdata import TestCtxMgrClassAsyncPPWrapper, TestCtxMgrClassAsyncPPWrapper2


class AsyncCtxMgrBaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_asyncctxmgrclass_runsasynchronously(self):
        cm = TestCtxMgrClassAsyncPPWrapper()
        async with cm:
            asyncio.sleep(0)
        self.assertEqual(cm.is_done, True)
        self.assertEqual(cm.is_async_done, True)

    async def test_asyncctxmgrclass_withcallclosenotset_runsasynchronously(self):
        cm = TestCtxMgrClassAsyncPPWrapper2()
        async with cm:
            asyncio.sleep(0)
        self.assertEqual(cm.is_done, True)
        self.assertEqual(cm.is_async_done, False)


if __name__ == "__main__":
    unittest.main()
