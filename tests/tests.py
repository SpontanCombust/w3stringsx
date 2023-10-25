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
    

class Tests(unittest.TestCase):
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

    def test_encode_abbreviated_no_header(self):
        self.run_case('encode_abbreviated_no_header', '-l pl -k')

    def test_encode_keep_csv(self):
        self.run_case('encode_keep_csv', '-l esmx -k')

    def test_encode_vanilla(self):
        self.run_case('encode_vanilla', '-l en')

    def test_encode_mixed(self):
        self.run_case('encode_mixed', '-l en -k')

    def test_encode_mixed_overlap(self):
        self.run_case('encode_mixed_overlap', '-l en -k')

    def test_parse_xml(self):
        self.run_case('parse_xml')

    def test_parse_xml_custom_names(self):
        self.run_case('parse_xml_custom_names')

    def test_decode_with_file_output(self):
        self.run_case('decode_with_file_output', output_path='decoded.csv')

    def test_parse_xml_with_file_output(self):
        self.run_case('parse_xml_with_file_output', output_path='parsed.csv')

    def test_decode_path_with_spaces(self):
        self.run_case('decode path with spaces')

    def test_encode_path_with_spaces(self):
        self.run_case('encode path with spaces', '-l en')

    def test_parse_ws(self):
        self.run_case('parse_ws', '-s "^ibt_"')

    def test_parse_xml_search(self):
        self.run_case('parse_xml_search', '--search "MOD"')

    def test_parse_xml_non_localized(self):
        self.run_case('parse_xml_non_localized')

    def test_parse_xml_bundled_items(self):
        self.run_case('parse_xml_bundled_items')

    def test_parse_dir(self):
        self.run_case('parse_dir', '-s "(Mods|ibt_)"')

    def test_parse_dir_merge(self):
        self.run_case('parse_dir_merge', '-s "(Mods|ibt_)"')

    def test_parse_dir_merge_no_sections(self):
        self.run_case('parse_dir_merge_no_sections', '-s "(Mods|ibt_)"')


    def run_case(self, case_name: str, extra_args: str = '', output_path: str | None = None, see_output: bool = False):
        root_dir = os.path.abspath(os.path.join(__file__, '../../'))
        case_dir = f"{root_dir}/tests/{case_name}"

        input_dir = f"{case_dir}/input"
        output_dir = f"{case_dir}/output"
        output_preload_dir = f"{case_dir}/output_preload"
        expected_dir = f"{case_dir}/expected"

        input_path = f"{input_dir}/{os.listdir(input_dir)[0]}"
        output_path = f"{output_dir}/{output_path}" if output_path is not None else output_dir

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        if os.path.exists(output_preload_dir):
            output_preload_path = f"{output_preload_dir}/{os.listdir(output_preload_dir)[0]}"
            shutil.copy(output_preload_path, output_dir)
        
        cmd = f'python {root_dir}/src/w3stringsx.py "{input_path}" -o "{output_path}" {extra_args}'
        try:
            subprocess.run(cmd, shell=True, check=True, stdout=(None if see_output else subprocess.DEVNULL))
        except:
            pass

        try:
            self.assert_output(expected_dir, output_dir)
        finally:
            if not see_output:
                for output in os.listdir(output_dir):
                    output_path = os.path.join(output_dir, output)
                    os.remove(output_path)


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