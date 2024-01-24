import sys
import unittest
sys.path.append("..\\unblock")
from unblock.io import aopen
from unblock.tempfile import AsyncTemporaryFile


class TestIO(unittest.IsolatedAsyncioTestCase):

    async def test_file_read(self):
        fpth = r"tests\data\sample_text.txt"
        async with await aopen(fpth, 'r') as f:
            data = await f.read()
            self.assertEqual(data, 'A quick brown fox jumps over the lazy log')

    async def test_multilinefile_read(self):
        fpth = r"tests\data\multiline_text.txt"
        lines = []
        async with await aopen(fpth, 'r') as f:
            async for line in f:
                lines.append(line)
        self.assertEqual(lines, ['line1\n', 'line2\n', 'line3\n'])

    async def test_tempfile_binarywrite(self):
        async with AsyncTemporaryFile() as fd:
            await fd.write(b'A quick brown fox jumps over the lazy log')
            await fd.seek(0)
            data = await fd.read1()
            self.assertEqual(data, b'A quick brown fox jumps over the lazy log')


if __name__ == "__main__":
    unittest.main()