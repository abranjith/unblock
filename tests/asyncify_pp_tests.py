import unittest
from tests.testdata import asyncifypp_test_sync_func


class AsyncifyPPDecoratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_asyncifypp_function_returnscoro(self):
        expected = "test_sync_func"
        async_resp = await asyncifypp_test_sync_func()
        self.assertEqual(expected, async_resp)


if __name__ == "__main__":
    unittest.main()
