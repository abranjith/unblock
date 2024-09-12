import unittest
import asyncio
from tests.testdata import TestAsyncProperty

class AsyncCtxMgrBaseTests(unittest.IsolatedAsyncioTestCase):
   async def test_asyncproperty_runsasynchronously(self):
      expected = "prop"
      obj = TestAsyncProperty(expected)
      actual = await obj.prop
      self.assertEqual(expected, actual)
      #changing property should reflect
      new_val = "new value"
      obj.set_prop(new_val)
      actual = await obj.prop
      self.assertEqual(new_val, actual)

   async def test_asynccachedproperty_runsasynchronously(self):
      expected = "prop"
      obj = TestAsyncProperty(expected)
      actual = await obj.cached_prop
      self.assertEqual(expected, actual)
      #changing property should not reflect (instead returns already cachd property)
      new_val = "new value"
      obj.set_prop(new_val)
      actual = await obj.cached_prop
      self.assertEqual(expected, actual)

if __name__ == "__main__":
   unittest.main()