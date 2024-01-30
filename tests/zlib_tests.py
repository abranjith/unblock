import sys
import unittest
import zlib
sys.path.append("..\\unblock")
from unblock.zlib import compress, decompress, adler32


class TestZlib(unittest.IsolatedAsyncioTestCase):

    async def test_compress_and_decompress(self):
        ip = b'A quick brown fox jumps over the lazy log'
        cd = await compress(ip)
        dc = await decompress(cd)
        self.assertEqual(dc, ip)

    async def test_checksum(self):
        ip = b'A quick brown fox jumps over the lazy log'
        sync_cs = zlib.adler32(ip)
        async_cs = await adler32(ip)
        self.assertEqual(sync_cs, async_cs)


if __name__ == "__main__":
    unittest.main()
