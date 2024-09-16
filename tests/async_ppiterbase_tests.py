import unittest
from tests.testdata import TestIterClassAsyncPPWrapper


class AsyncPPIterBaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_asyncppiterclass_runsasynchronously(self):
        expected = [1, 2, 3, 4, 5]
        iter = TestIterClassAsyncPPWrapper(1, 6)
        actual = []
        async for i in iter:
            actual.append(i)
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
