import unittest
from tests.testdata import TestCtxMgrIterClassAsyncWrapper

class AsyncCtxMgrIterBaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_asyncitrctxmgrclass_runsasynchronously(self):
        cmi = TestCtxMgrIterClassAsyncWrapper(1, 6)
        expected = [1, 2, 3, 4, 5]
        actual = []
        async with cmi:
            async for i in cmi:
                actual.append(i)
        self.assertEqual(cmi.is_done, True)
        self.assertEqual(cmi.is_async_done, True)
        self.assertEqual(expected, actual)

if __name__ == "__main__":
    unittest.main()
