import unittest
from tests.testdata import TestIterClassAsyncWrapper

class AsyncIterBaseTests(unittest.IsolatedAsyncioTestCase):
    
    async def test_asynciterclass_runsasynchronously(self):
       expected = [1, 2, 3, 4, 5]
       iter = TestIterClassAsyncWrapper(1, 6)
       actual = []
       async for i in iter:
          actual.append(i)
       self.assertEqual(expected, actual)
    
if __name__ == "__main__":
    unittest.main()
