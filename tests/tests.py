# This file should be run from the root of this project

import hashlib
import io
import os
import shutil
import subprocess
import unittest

def file_hash(file_path: str) -> str:
    with io.open(file_path, 'rb') as f:
        data = f.read()
        md5 = hashlib.md5(data)
        return md5.hexdigest()
    

class TestW3Stringsx(unittest.TestCase):
    def test_decode_en(self):
        self.run_case('case1')

    def test_decode_pl(self):
        self.run_case('case2')



    def run_case(self, case_name: str, extra_args: str = ''):
        case_dir = f"./tests/{case_name}"
        input_file = os.listdir(f"{case_dir}/input")[0]
        input_file_path = os.path.join(f"{case_dir}/input", input_file)
        output_dir = f"{case_dir}/output"
        expected_dir = f"{case_dir}/expected"
        
        cmd = f"python ./src/w3stringsx.py {input_file_path} -o {output_dir} {extra_args}"
        try:
            subprocess.run(cmd, shell=True, check=True)
        except Exception as e:
            print(e)

        try:
            self.assert_output(expected_dir, output_dir)
        except Exception as e:
            raise e
        finally:
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)


    def assert_same_files(self, f1: str, f2: str):
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))

        f1_hash = file_hash(f1)
        f2_hash = file_hash(f2)
        self.assertEqual(f1_hash, f2_hash)

    def assert_output(self, expected_dir: str, output_dir: str):
        self.assertTrue(os.path.exists(output_dir))

        expected_files = os.listdir(expected_dir)
        expected_files.sort()

        output_files = os.listdir(output_dir)
        output_files.sort()

        self.assertEqual(expected_files, output_files)

        for i in range(len(expected_files)):
            e = os.path.join(expected_dir, expected_files[i])
            o = os.path.join(output_dir, output_files[i]) 
            self.assert_same_files(e, o)
   

if __name__ == '__main__':
    unittest.main()