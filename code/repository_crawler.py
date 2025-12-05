import os
import json
import yaml
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from typing import List, Dict, Any, Optional

# 配置文件路径常量
CONFIG_PATH = '../configs/config.yaml'
OUTPUT_DIR = '../data/raw_data/repos'

def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件并验证结构"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # 验证必要配置项
        required = {'github': {'token'}, 'crawl_repos':{}}
        for req_key, req_subkeys in required.items():
            if req_key not in config:
                raise ValueError(f"Missing '{req_key}' section in config")
            if isinstance(config[req_key], dict):
                for subkey in req_subkeys:
                    if subkey not in config[req_key]:
                        raise ValueError(f"Missing '{req_key}.{subkey}' in config")
        
        return config
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Config file not found at {config_path}. "
            "Please create config.yaml with structure:\n\n"
            "github:\n"
            "  token: 'your_github_token_here'\n"
            "crawl_repos:\n"
            "  - 'owner/repo1'\n"
            "  - 'owner/repo2'"
        )
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format: {e}")

def get_github_repo(repo_url: str, token: str) -> Dict[str, Any]:
    """获取GitHub仓库基本信息"""
    request = Request(repo_url)
    request.add_header('Authorization', f'token {token}')
    request.add_header('User-Agent', 'ERNIE-X1.1')
    request.add_header('Accept', 'application/vnd.github.v3+json')
    
    try:
        with urlopen(request) as response:
            if response.status != 200:
                raise HTTPError(response.url, response.status, "GitHub API error", None, None)
            return json.loads(response.read().decode())
    except HTTPError as e:
        raise Exception(f"GitHub API error ({e.code}): {e.reason}")
    except URLError as e:
        raise Exception(f"Network error: {e.reason}")

def get_repo_files(repo_owner: str, repo_name: str, token: str, path: str = '') -> List[Dict[str, Any]]:
    """递归获取仓库所有文件列表（含分页处理）"""
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}'
    files = []
    
    while url:
        request = Request(url)
        request.add_header('Authorization', f'token {token}')
        request.add_header('User-Agent', 'ERNIE-X1.1')
        
        try:
            with urlopen(request) as response:
                if response.status != 200:
                    break
                    
                data = json.loads(response.read().decode())
                for item in data:
                    if item['type'] == 'file':
                        files.append({
                            'path': item['path'],
                            'download_url': item['download_url'],
                            'size': item['size']
                        })
                    elif item['type'] == 'dir':
                        subdir_files = get_repo_files(repo_owner, repo_name, token, item['path'])
                        files.extend(subdir_files)
                
                # 处理分页
                link_header = response.headers.get('Link', '')
                url = None
                if link_header:
                    next_link = [link.strip() for link in link_header.split(',') 
                                if 'rel="next"' in link]
                    if next_link:
                        url = next_link[0].split(';')[0].strip('<>')
                        
        except HTTPError as e:
            print(f"\nWarning: Skipping {repo_name}/{path} due to HTTP {e.code}")
            break
        except URLError as e:
            print(f"\nWarning: Skipping {repo_name}/{path} due to network error")
            break
    
    return files

def save_crawl_result(owner: str, repo_name: str, repo_info: Dict, files: List) -> None:
    """保存爬取结果到JSON文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f'{owner}_{repo_name}.json')
    
    result = {
        'repo_info': repo_info,
        'files': files,
        'crawl_timestamp': datetime.now().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Saved {len(files)} files for {repo_name}")

def main():
    print("Starting GitHub repository crawler...\n")
    print(f"Using config: {CONFIG_PATH}\n")
    
    try:
        # 加载配置
        config = load_config(CONFIG_PATH)
        token = config['github']['token']
        repos = config['crawl_repos']
        
        print(f"Config loaded. Token ends with: {token[-4:]}")
        print(f"Target repositories: {', '.join(repos)}\n")
        
        # 遍历所有仓库
        for i, repo in enumerate(repos, 1):
            owner, repo_name = repo.split('/')
            repo_url = f'https://api.github.com/repos/{owner}/{repo_name}'
            
            try:
                print(f"Processing [{i}/{len(repos)}] {repo_name}...")
                
                # 获取仓库基本信息
                repo_info = get_github_repo(repo_url, token)
                print(f"  Fetched repo info: {repo_info['html_url']}")
                
                # 获取文件列表
                files = get_repo_files(owner, repo_name, token)
                print(f"  Found {len(files)} files")
                
                # 保存结果
                save_crawl_result(owner, repo_name, repo_info, files)
                
            except Exception as e:
                print(f"  Error processing {repo_name}: {str(e)}")
                continue
        
        print("\nCrawler completed successfully!")
        
    except Exception as e:
        print(f"\nCritical error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    import datetime
    main()