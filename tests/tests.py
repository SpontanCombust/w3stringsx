# This file should be run from the root of this project
# Put the encoder itself somewhere in the PATH so that w3stringsx can find it

import hashlib
import io
import os
import subprocess
import sys
import unittest

def file_hash(file_path: str) -> str:
    with io.open(file_path, 'rb') as f:
        data = f.read()
        md5 = hashlib.md5(data)
        return md5.hexdigest()
    

class TestW3Stringsx(unittest.TestCase):
    def test_decode_en(self):
        self.run_case('decode_en')

    def test_decode_pl(self):
        self.run_case('decode_pl')

    def test_encode_en(self):
        self.run_case('encode_en')

    def test_encode_pl(self):
        self.run_case('encode_pl')

    def test_encode_only_pl(self):
        self.run_case('encode_only_pl', "-l pl")

    def test_encode_pl_no_header(self):
        self.run_case('encode_pl_no_header', "-l pl")

    def test_encode_pl_from_header(self):
        self.run_case('encode_pl_from_header', "-l pl")

    def test_encode_default_lang(self):
        self.run_case('encode_default_lang')

    def test_encode_abbreviated(self):
        self.run_case('encode_abbreviated', '-l esmx')

    def test_encode_keep_csv(self):
        self.run_case('encode_keep_csv', '-l esmx -k')

    def test_encode_vanilla(self):
        self.run_case('encode_vanilla', '-l en')

    def test_encode_mixed(self):
        self.run_case('encode_mixed', '-l en -k')

    def test_parse_xml(self):
        self.run_case('parse_xml')

    def test_parse_xml_custom_names(self):
        self.run_case('parse_xml_custom_names')

    def test_decode_with_file_output(self):
        self.run_case('decode_with_file_output', output_file='decoded.csv')

    def test_parse_xml_with_file_output(self):
        self.run_case('parse_xml_with_file_output', output_file='parsed.csv')


    def run_case(self, case_name: str, extra_args: str = '', output_file: str | None = None):
        print(f"Running test case {case_name}")

        case_dir = f"./tests/{case_name}"
        input_file = os.listdir(f"{case_dir}/input")[0]
        input_file_path = os.path.join(f"{case_dir}/input", input_file)
        output_dir = f"{case_dir}/output"
        output_path = f"{output_dir}/{output_file}" if output_file is not None else output_dir
        expected_dir = f"{case_dir}/expected"

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        
        cmd = f"python ./src/w3stringsx.py {input_file_path} -o {output_path} {extra_args}"
        try:
            subprocess.run(cmd, shell=True, check=True)
        except Exception as e:
            print(e, file=sys.stderr)

        try:
            self.assert_output(expected_dir, output_dir)
        except Exception as e:
            raise e
        finally:
            for output in os.listdir(output_dir):
                output_path = os.path.join(output_dir, output)
                os.remove(output_path)

        print()


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