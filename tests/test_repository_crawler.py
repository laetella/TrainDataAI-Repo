# test_repository_crawler.py  
# # 测试代码仓库爬取功能的脚本
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import yaml
import sys
sys.path.append('../code')

from repository_crawler import (
    load_config,
    get_github_repo,
    get_repo_files,
    save_crawl_result,
    main
)

class TestRepositoryCrawler(unittest.TestCase):
    VALID_CONFIG = """
github:
  token: ghp_test_token
crawl_repos:
  - baidu/ERNIE-X1
  - tensorflow/tensorflow
"""
    INVALID_CONFIG = "invalid_yaml"
    CONFIG_PATH = "test_config.yaml"
    OUTPUT_DIR = "test_output"

    def setUp(self):
        """创建测试配置文件"""
        with open(self.CONFIG_PATH, 'w') as f:
            f.write(self.VALID_CONFIG)

    def tearDown(self):
        """清理测试文件"""
        if os.path.exists(self.CONFIG_PATH):
            os.remove(self.CONFIG_PATH)
        if os.path.exists(self.OUTPUT_DIR):
            os.rmdir(self.OUTPUT_DIR)

    # 测试配置加载模块
    def test_load_config_valid(self):
        config = load_config(self.CONFIG_PATH)
        self.assertIn('github', config)
        self.assertIn('crawl_repos', config)
        self.assertEqual(config['github']['token'], 'ghp_test_token')

    def test_load_config_missing_section(self):
        with open(self.CONFIG_PATH, 'w') as f:
            f.write("crawl_repos:\n  - test/repo")
        with self.assertRaises(ValueError) as context:
            load_config(self.CONFIG_PATH)
        self.assertIn("Missing 'github' section", str(context.exception))

    def test_load_config_invalid_yaml(self):
        with open(self.CONFIG_PATH, 'w') as f:
            f.write(self.INVALID_CONFIG)
        with self.assertRaises(ValueError) as context:
            load_config(self.CONFIG_PATH)
        self.assertIn("Invalid YAML format", str(context.exception))

    # 测试GitHub API请求模块
    @patch('urllib.request.urlopen')
    def test_get_github_repo_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.getheader.return_value = "application/json"
        mock_response.read.return_value = b'{"name": "test_repo"}'
        mock_urlopen.return_value = mock_response

        result = get_github_repo(
            "https://api.github.com/repos/test/repo",
            "test_token"
        )
        self.assertEqual(result, {"name": "test_repo"})

    @patch('urllib.request.urlopen')
    def test_get_github_repo_http_error(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 401
        mock_urlopen.side_effect = HTTPError(
            "url", 401, "Unauthorized", None, None
        )
        with self.assertRaises(Exception) as context:
            get_github_repo("https://api.github.com/repos/test/repo", "invalid_token")
        self.assertIn("GitHub API error (401): Unauthorized", str(context.exception))

    # 测试文件列表获取模块
    @patch('urllib.request.urlopen')
    def test_get_repo_files_single_file(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'''[
            {"type": "file", "path": "README.md", "download_url": "https://..."}
        ]'''
        mock_response.headers = {'Link': ''}
        mock_urlopen.return_value = mock_response

        files = get_repo_files("test", "repo", "token")
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]['path'], "README.md")

    @patch('urllib.request.urlopen')
    def test_get_repo_files_recursive(self, mock_urlopen):
        # 第一次响应：包含文件和目录
        mock_response1 = MagicMock()
        mock_response1.status = 200
        mock_response1.read.return_value = b'''[
            {"type": "dir", "path": "src"},
            {"type": "file", "path": "README.md"}
        ]'''
        
        # 第二次响应：目录内容
        mock_response2 = MagicMock()
        mock_response2.status = 200
        mock_response2.read.return_value = b'''[
            {"type": "file", "path": "src/main.py"}
        ]'''
        mock_response2.headers = {'Link': ''}
        
        mock_urlopen.side_effect = [mock_response1, mock_response2]
        
        files = get_repo_files("test", "repo", "token")
        self.assertEqual(len(files), 2)
        self.assertEqual(files[1]['path'], "src/main.py")

    # 测试结果保存模块
    @patch("builtins.open", new_callable=mock_open)
    def test_save_crawl_result(self, mock_file):
        mock_datetime = MagicMock()
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"
        
        with patch('repository_crawler.datetime', mock_datetime):
            save_crawl_result(
                "test", "repo", 
                {"html_url": "https://github.com/test/repo"}, 
                [{"path": "README.md"}]
            )
            
        mock_file.assert_called_once_with(
            os.path.join(self.OUTPUT_DIR, "test_repo.json"), 'w'
        )
        result = json.loads(mock_file().write.call_args[0][0])
        self.assertEqual(result['repo_info']['html_url'], "https://github.com/test/repo")
        self.assertEqual(result['files'][0]['path'], "README.md")
        self.assertEqual(result['crawl_timestamp'], "2023-01-01T00:00:00")

    # 测试主流程
    @patch('repository_crawler.get_github_repo')
    @patch('repository_crawler.get_repo_files')
    @patch('repository_crawler.save_crawl_result')
    def test_main_success(self, mock_save, mock_files, mock_repo):
        mock_repo.return_value = {"name": "test_repo"}
        mock_files.return_value = [{"path": "README.md"}]
        
        with patch('builtins.print') as mock_print, \
             patch('repository_crawler.CONFIG_PATH', self.CONFIG_PATH), \
             patch('repository_crawler.OUTPUT_DIR', self.OUTPUT_DIR):
            
            main()
            
            self.assertEqual(mock_repo.call_count, 2)  # 两个仓库
            self.assertEqual(mock_files.call_count, 2)
            mock_save.assert_called()
            mock_print.assert_any_call("Crawler completed successfully!")

if __name__ == "__main__":
    unittest.main(verbosity=2)