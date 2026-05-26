import ast
import os
import pytest

def get_py_files(src_dir):
    py_files = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files

@pytest.mark.parametrize("file_path", get_py_files("src"))
def test_no_unsafe_dynamic_execution_or_subprocesses(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename=file_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check for exec() or eval()
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                assert func_name != "exec", f"Unsafe exec() usage found in {file_path}"
                assert func_name != "eval", f"Unsafe eval() usage found in {file_path}"

            # Check for subprocess calls
            func_name = ""
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id

            if func_name in ("run", "Popen", "call", "check_call", "check_output"):
                # Ensure shell=True is not passed or is False
                for kw in node.keywords:
                    if kw.arg == "shell":
                        if isinstance(kw.value, ast.Constant):
                            assert kw.value.value is False, f"Unsafe shell=True found in {file_path}"
