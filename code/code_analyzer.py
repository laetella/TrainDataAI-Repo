# 代码分析脚本，用于解析代码文件，提取函数信息
import ast
import os
from typing import List, Dict, Any
import json
import re
import requests

class FunctionAnalyzer(ast.NodeVisitor):
    """AST节点访问器，用于提取函数定义信息"""
    def __init__(self):
        self.functions = []
        
    def visit_FunctionDef(self, node):
        """处理函数定义节点"""
        func_data = {
            'name': node.name,
            'params': [arg.arg for arg in node.args.args],
            'body': ast.unparse(node.body),
            'lineno': node.lineno,
            'docstring': ast.get_docstring(node)
        }
        self.functions.append(func_data)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """处理异步函数定义"""
        self.visit_FunctionDef(node)

def analyze_code_file(file_path: str) -> List[Dict[str, Any]]:
    """解析代码文件并提取函数信息
    
    Args:
        file_path: 代码文件路径
        
    Returns:
        List[Dict]: 包含函数信息的字典列表，每个字典包含：
            - name: 函数名
            - params: 参数列表
            - body: 函数体代码
            - lineno: 起始行号
            - docstring: 文档字符串
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Code file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
            
        tree = ast.parse(code)
        analyzer = FunctionAnalyzer()
        analyzer.visit(tree)
        return analyzer.functions
    except SyntaxError as e:
        raise ValueError(f"Invalid syntax in {file_path}: {e}")
    except Exception as e:
        raise RuntimeError(f"Error analyzing {file_path}: {e}")

def analyze_directory(dir_path: str) -> List[Dict[str, Any]]:
    """递归分析目录中的所有代码文件"""
    results = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith(('.py', '.js', '.java')):
                file_path = os.path.join(root, file)
                try:
                    results.extend(analyze_code_file(file_path))
                except Exception as e:
                    print(f"Skipping {file_path}: {str(e)}")
    return results
import urllib.request
from urllib.error import URLError

def download_content(base_dir, url, name):
    """从URL下载原始内容并处理异常"""
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                data = response.read().decode()
                # print("====",response.read().decode())
                with open(os.path.join(base_dir,name), 'w') as f:
                    f.write(data)
                # data = json.loads(response.read().decode()) # 'utf-8'
                # print("download content data: ", data)
                # for item in data:
                #     print("item: ", item)
                #     input()
                return data
            else:
                print(f"HTTP {response.status} 错误: {url}")
    except URLError as e:
        print(f"下载失败 {url}: {e.reason}")
    return None

def extract_functions(content, file_type):
    """根据文件类型提取函数定义"""
    if file_type == '.py':
        # 使用AST解析Python代码
        tree = ast.parse(content)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node)
                })
        return functions
    
    elif file_type in ['.js', '.ts']:
        # 使用正则表达式匹配JavaScript函数
        pattern = r'function\s+(\w+)\s*\(([^)]*)\)'
        return [{'name': match[0], 'args': match[1].split(',')} 
                for match in re.findall(pattern, content)]
    
    else:
        return []  # 暂不支持其他类型

def get_functions(raw_json_path):
    # 示例：从保存的JSON中读取URL并下载
    base_dir = '../data2/raw_data/repos/tensorflow/' # 代码下载的根目录
    os.makedirs(base_dir, exist_ok=True)
    with open(raw_json_path) as f:
        next(f) # 跳过第一行，todo： 文件为空的情况需要处理
        for line in f:
            file_info = json.loads(line)
            # print(file_info.items())
            temp_url = file_info['download_url']
            if temp_url.endswith(('.py', '.cc', '.h', '.js', '.java', '.sh')):
                # name = file_info['path'].split('/')[0][1:] #因为都是以. 开始的，所以从1开始，有很多重复的文件名
                name = temp_url.split('/')[-1]
                content = download_content(base_dir, temp_url, name)# 最后一个参数为代码的path，可作为代码名字存放
                # print("content: ", content)
                # input()

if __name__ == '__main__':
    # step 2 : from urls get function
    raw_json_path = "../data2/raw_data/repos/tensorflow/tensorflow.json"
    get_functions(raw_json_path)
    # results = analyze_code_file(file_path)
    # print(results)
    # # 示例使用
    # py_content = "def add(a, b):\n    'sum two numbers'\n    return a+b"
    # print(extract_functions(py_content, '.py'))
