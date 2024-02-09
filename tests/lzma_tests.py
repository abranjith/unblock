import sys
import unittest
sys.path.append("..\\unblock")
from unblock.lzma import compress, decompress


class TestLzma(unittest.IsolatedAsyncioTestCase):

    async def test_compress_and_decompress(self):
        ip = b'A quick brown fox jumps over the lazy log'
        cd = await compress(ip)
        dc = await decompress(cd)
        self.assertEqual(dc, ip)


if __name__ == "__main__":
    unittest.main()