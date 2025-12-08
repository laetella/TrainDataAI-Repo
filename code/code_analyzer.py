# 代码分析脚本，用于解析代码文件，提取函数信息
import ast
import os
from typing import List, Dict, Any
import json
import re
import requests
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
            function_extensions = ('.c', '.h', '.cpp', '.cxx', '.cc', '.hpp', '.ipp', '.java', '.py', '.pyw', '.R', '.sh', '.bash', '.zsh', '.cs', '.go', '.rs', '.scala')
            if temp_url.endswith(function_extensions):
                name = temp_url.split('/')[-1]
                # name = file_info['path'].split('/')[0][1:] #因为都是以. 开始的，所以从1开始，有很多重复的文件名
                if not os.path.exists(os.path.join(base_dir,name)):
                    print("now save file: ", name)
                    content = download_content(base_dir, temp_url, name)# 最后一个参数为代码的path，可作为代码名字存放
                # print("content: ", content)
                # input()
import ast
import os
import re
from typing import List, Dict, Any
import traceback

# 支持的语言及其文件扩展名
SUPPORTED_EXTENSIONS = {
    # Python系列
    '.py': 'python',
    '.pyw': 'python',  # Windows无控制台窗口
    
    # JavaScript/TypeScript
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'javascript',
    '.tsx': 'typescript',
    
    # Java系列
    '.java': 'java',
    
    # C/C++系列
    '.c': 'c',
    '.h': 'c',      # C头文件
    '.cpp': 'cpp',  # C++标准源码
    '.cxx': 'cpp',  # C++常见变体
    '.cc': 'cpp',   # C++常见变体
    '.hpp': 'cpp',  # C++头文件
    '.ipp': 'cpp',  # C++模板实现
    
    # 其他语言
    '.go': 'go',
    '.rs': 'rust',
    '.cs': 'csharp',
    '.swift': 'swift',
    '.php': 'php',
    '.rb': 'ruby',
    '.R': 'r',      # R语言
    '.scala': 'scala',
    
    # Shell脚本
    '.sh': 'shell',
    '.bash': 'shell',
    '.zsh': 'shell'
}

def analyze_python_code(content: str) -> List[Dict[str, Any]]:
    """分析Python代码"""
    functions = []
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            # 处理函数定义
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = {
                    'name': node.name,
                    'language': 'python',
                    'params': [arg.arg for arg in node.args.args],
                    'lineno': node.lineno,
                    'docstring': ast.get_docstring(node),
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                }
                functions.append(func_info)
                
            # 处理类方法
            elif isinstance(node, ast.ClassDef):
                for subnode in node.body:
                    if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_info = {
                            'name': f"{node.name}.{subnode.name}",
                            'language': 'python',
                            'params': [arg.arg for arg in subnode.args.args],
                            'lineno': subnode.lineno,
                            'docstring': ast.get_docstring(subnode),
                            'is_async': isinstance(subnode, ast.AsyncFunctionDef),
                        }
                        functions.append(func_info)
    except SyntaxError:
        pass  # 忽略语法错误
    return functions

def analyze_javascript_code(content: str) -> List[Dict[str, Any]]:
    """分析JavaScript/TypeScript代码"""
    functions = []
    
    # 普通函数：function name() {}
    pattern1 = r'function\s+(\w+)\s*\(([^)]*)\)'
    # 箭头函数：const name = () => {}
    pattern2 = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>'
    # 类方法：methodName() {}
    pattern3 = r'(\w+)\s*\(([^)]*)\)\s*\{'
    # TypeScript函数：function name(param: type): returnType {}
    pattern4 = r'function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*\w+)?\s*\{'
    
    for pattern in [pattern1, pattern2, pattern3, pattern4]:
        for match in re.finditer(pattern, content, re.MULTILINE):
            params_str = match.group(2).strip()
            params = [p.strip().split(':')[0] for p in params_str.split(',') if p.strip()]
            
            func_info = {
                'name': match.group(1),
                'language': 'javascript',
                'params': params,
                'lineno': content[:match.start()].count('\n') + 1,
                'docstring': None,
            }
            functions.append(func_info)
    
    return functions

def analyze_java_code(content: str) -> List[Dict[str, Any]]:
    """分析Java代码"""
    functions = []
    
    # Java方法：public|private|protected ReturnType methodName(params) {}
    pattern = r'(?:public|private|protected|static|\s)+([\w<>[\]]+)\s+(\w+)\s*\(([^)]*)\)'
    
    for match in re.finditer(pattern, content):
        return_type = match.group(1).strip()
        method_name = match.group(2)
        params_str = match.group(3).strip()
        
        # 解析参数
        params = []
        if params_str:
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    # 提取参数名（最后一个单词）
                    parts = param.split()
                    if parts:
                        param_name = parts[-1]
                        params.append(param_name)
        
        func_info = {
            'name': method_name,
            'language': 'java',
            'params': params,
            'return_type': return_type,
            'lineno': content[:match.start()].count('\n') + 1,
            'docstring': extract_java_docstring(content, match.start()),
        }
        functions.append(func_info)
    
    return functions

def analyze_cpp_code(content: str) -> List[Dict[str, Any]]:
    """分析C/C++代码"""
    functions = []
    
    # C/C++函数：ReturnType functionName(params) {}
    pattern = r'(\w+(?:\s*::\s*\w+)*)\s+(\w+)\s*\(([^)]*)\)\s*(?:const\s*)?\{'
    
    for match in re.finditer(pattern, content):
        return_type = match.group(1).strip()
        func_name = match.group(2)
        params_str = match.group(3).strip()
        
        params = []
        if params_str:
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    # 提取参数名（最后一个单词）
                    parts = param.split()
                    if parts:
                        param_name = parts[-1].strip('*&')  # 去掉指针/引用符号
                        params.append(param_name)
        
        func_info = {
            'name': func_name,
            'language': 'cpp',
            'params': params,
            'return_type': return_type,
            'lineno': content[:match.start()].count('\n') + 1,
            'docstring': extract_cpp_docstring(content, match.start()),
        }
        functions.append(func_info)
    
    return functions

def extract_java_docstring(content: str, position: int) -> str:
    """提取Java文档注释"""
    # 查找position之前的文档注释 /** ... */
    lines = content[:position].split('\n')
    doc_lines = []
    
    for line in reversed(lines):
        stripped = line.strip()
        if stripped.startswith('*/'):
            continue
        elif stripped.startswith('*'):
            doc_lines.append(stripped[1:].strip())
        elif stripped.startswith('/**'):
            break
        else:
            break
    
    return '\n'.join(reversed(doc_lines)) if doc_lines else None

def extract_cpp_docstring(content: str, position: int) -> str:
    """提取C++文档注释"""
    # 支持 // 和 /* */ 注释
    lines = content[:position].split('\n')
    doc_lines = []
    
    for line in reversed(lines[:3]):  # 只检查前3行
        stripped = line.strip()
        if stripped.startswith('//'):
            doc_lines.append(stripped[2:].strip())
        else:
            break
    
    return '\n'.join(reversed(doc_lines)) if doc_lines else None

def analyze_code_by_language(content: str, language: str) -> List[Dict[str, Any]]:
    """根据语言类型调用相应的分析函数"""
    if language == 'python':
        return analyze_python_code(content)
    elif language in ['javascript', 'typescript']:
        return analyze_javascript_code(content)
    elif language == 'java':
        return analyze_java_code(content)
    elif language in ['cpp', 'c']:
        return analyze_cpp_code(content)
    elif language == 'go':
        return analyze_golang_code(content)
    elif language == 'rust':
        return analyze_rust_code(content)
    else:
        # 对于不支持的语言，尝试通用分析
        return analyze_generic_code(content)

def analyze_generic_code(content: str) -> List[Dict[str, Any]]:
    """通用代码分析（用于不支持的语言）"""
    functions = []
    
    # 通用函数模式：单词后面跟着括号
    pattern = r'(\b\w+\b)\s*\(([^)]*)\)\s*\{'
    
    for match in re.finditer(pattern, content):
        func_name = match.group(1)
        params_str = match.group(2).strip()
        
        params = []
        if params_str:
            params = [p.strip() for p in params_str.split(',') if p.strip()]
        
        func_info = {
            'name': func_name,
            'language': 'unknown',
            'params': params,
            'lineno': content[:match.start()].count('\n') + 1,
            'docstring': None,
        }
        functions.append(func_info)
    
    return functions

def analyze_code_file(file_path: str) -> List[Dict[str, Any]]:
    """解析代码文件并提取函数信息"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 获取文件扩展名和语言类型
    ext = os.path.splitext(file_path)[1].lower()
    language = SUPPORTED_EXTENSIONS.get(ext, 'unknown')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 根据语言类型调用相应的分析函数
        functions = analyze_code_by_language(content, language)
        
        # 添加文件信息
        for func in functions:
            func['file'] = os.path.basename(file_path)
            func['file_path'] = file_path
            func['language'] = language
        
        return functions
        
    except SyntaxError as e:
        print(f"语法错误 {file_path}: {e}")
        return []
    except Exception as e:
        print(f"分析错误 {file_path}: {e}")
        return []

def analyze_directory(dir_path: str, functions_path: str) -> List[Dict[str, Any]]:
    """递归分析目录中的所有代码文件"""
    results = []
    
    if not os.path.exists(dir_path):
        raise FileNotFoundError(f"目录不存在: {dir_path}")
    
    for root, _, files in os.walk(dir_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                file_path = os.path.join(root, file)
                try:
                    functions = analyze_code_file(file_path)
                    if functions:
                        # if not os.path.exists(functions_path):
                        #     with open(functions_path, "w", encoding="utf-8") as f:
                        #         json.dump(functions, f, indent=2)
                        # else:
                        #     with open(functions_path, "a", encoding="utf-8") as f:
                        #         json.dump(functions, f, indent=2)
                        results.extend(functions)
                        print(f"✓ 分析完成: {file_path} ({len(functions)}个函数)")
                except Exception as e:
                    print(f"✗ 跳过 {file_path}: {str(e)}")
    with open(functions_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return results

# 以下是对Go和Rust的简单分析函数（可选添加）

def analyze_golang_code(content: str) -> List[Dict[str, Any]]:
    """分析Go代码"""
    functions = []
    
    # Go函数：func functionName(params) returnType {}
    pattern = r'func\s+(\w+)\s*\(([^)]*)\)(?:\s+([^{]+))?\s*\{'
    
    for match in re.finditer(pattern, content):
        func_name = match.group(1)
        params_str = match.group(2).strip()
        return_type = match.group(3).strip() if match.group(3) else None
        
        params = []
        if params_str:
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    parts = param.split()
                    if len(parts) >= 2:
                        params.append(parts[-1])  # 参数名
                    else:
                        params.append(param)
        
        func_info = {
            'name': func_name,
            'language': 'go',
            'params': params,
            'return_type': return_type,
            'lineno': content[:match.start()].count('\n') + 1,
            'docstring': None,
        }
        functions.append(func_info)
    
    return functions

def analyze_rust_code(content: str) -> List[Dict[str, Any]]:
    """分析Rust代码"""
    functions = []
    
    # Rust函数：fn function_name(params) -> return_type {}
    pattern = r'fn\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^{]+))?\s*\{'
    
    for match in re.finditer(pattern, content):
        func_name = match.group(1)
        params_str = match.group(2).strip()
        return_type = match.group(3).strip() if match.group(3) else None
        
        params = []
        if params_str:
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    # 格式：name: type
                    parts = param.split(':')
                    if len(parts) >= 2:
                        params.append(parts[0].strip())
        
        func_info = {
            'name': func_name,
            'language': 'rust',
            'params': params,
            'return_type': return_type,
            'lineno': content[:match.start()].count('\n') + 1,
            'docstring': None,
        }
        functions.append(func_info)
    
    return functions

if __name__ == '__main__':
    # # step 2 : from urls get function
    # raw_json_path = "../data2/raw_data/repos/tensorflow/tensorflow.json"
    # get_functions(raw_json_path)
    # step 3: analyze code
    dir_path = "../data2/raw_data/repos/tensorflow/"
    functions_path = "../data/analyze_function.json" # 分析函数的结果以json保存下来
    analyze_directory(dir_path, functions_path)
    # results = analyze_code_file(file_path)
    # print(results)
    # # 示例使用
    # py_content = "def add(a, b):\n    'sum two numbers'\n    return a+b"
    # print(extract_functions(py_content, '.py'))
