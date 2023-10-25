# Tests

Using `unittest` python package to test the tool.
Run `python ./tests.py` to run all tests or `python ./tests.py test_name` to test specific case.

Each test case runs on a basis of taking a file or directory from the `input` directory and passing it to w3stringsx, optionally together with some extra arguments. The output is saved in `output` directory. Test script then compares if the contents of `output` and `expected` directories are the same.<br>
Some test cases need files to be copied into `output` before w3stringsx executes. That's what optional directory `output_preload` is for. It is mainly used for testing entry merging.

Add `see_output=True` argument to `run_case`'s method call if you want to see the actual output in case of failed assertion. By default output files get deleted after a case finishes its work.