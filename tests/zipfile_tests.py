import unittest
import sys
sys.path.append("..\\unblock")
from unblock.zipfile import AsyncZipFile, AsyncZipInfo


class TestZipFile(unittest.IsolatedAsyncioTestCase):

    async def test_zipfile_listall(self):
        fpth = r"tests\data\test.zip"
        expected_files = ['sample_text.txt']
        async with await AsyncZipFile.create(fpth) as zfile:
            files = await zfile.namelist()
            self.assertListEqual(expected_files, files, "file name compare failed")

    async def test_zipfile_infoall(self):
        fpth = r"tests\data\test.zip"
        expected_files = ['sample_text.txt']
        async with await AsyncZipFile.create(fpth) as zfile:
            files = await zfile.infolist()
            for f in files:
                self.assertIsInstance(f, AsyncZipInfo)
                self.assertIn(f.filename, expected_files)

    async def test_zipfile_read(self):
        fpth = r"tests\data\test.zip"
        async with await AsyncZipFile.create(fpth) as zfile:
            async with await zfile.open("sample_text.txt") as myfile:
                data = await myfile.read()
                self.assertEqual(data, b'A quick brown fox jumps over the lazy log')


if __name__ == "__main__":
    unittest.main()