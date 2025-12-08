from typing import List, Dict, Any, Tuple, Optional
import re
import json

class DesignSolutionGenerator:
    """设计方案生成器（简洁版）"""
    
    def __init__(self):
        self.design_patterns = {
            'crud': {
                'name': 'CRUD操作',
                'components': ['Controller', 'Service', 'Repository', 'Model'],
                'description': '实现创建、读取、更新、删除操作的标准模式'
            },
            'mvc': {
                'name': 'MVC模式',
                'components': ['Model', 'View', 'Controller'],
                'description': '分离数据模型、用户界面和控制逻辑'
            },
            'repository': {
                'name': '仓储模式',
                'components': ['Repository', 'Entity', 'DataContext'],
                'description': '封装数据访问逻辑，提供统一的数据操作接口'
            },
            'factory': {
                'name': '工厂模式',
                'components': ['Factory', 'Product', 'ConcreteProduct'],
                'description': '通过工厂类创建对象，隐藏对象创建细节'
            }
        }

    def analyze_requirements(self, requirement_text):
        """分析需求"""
        pass
    
    def search_similar_solutions(self, requirement):
        """搜索相似解决方案"""
        pass
    
    def generate_design(self, context):
        """生成设计方案"""
        pass
    
    def generate_for_requirement(self, requirement: str, context: Dict) -> Dict:
        """为需求生成设计方案"""
        
        # 分析需求关键词
        keywords = self._extract_keywords(requirement)
        
        # 选择合适的设计模式
        pattern = self._select_design_pattern(keywords)
        
        # 生成设计方案
        solution = {
            'requirement': requirement,
            'design_pattern': pattern['name'],
            'description': pattern['description'],
            'components': self._generate_components(pattern, context),
            'implementation_steps': self._generate_steps(pattern, context),
            'integration_points': self._find_integration_points(context)
        }
        
        return solution
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取需求关键词"""
        keywords = []
        
        # 常见需求关键词
        common_keywords = [
            '增删改查', 'CRUD', '查询', '创建', '更新', '删除',
            '用户', '认证', '授权', '登录', '注册',
            '文件', '上传', '下载', '存储',
            '消息', '通知', '邮件', '短信',
            '缓存', '性能', '优化', '并发',
            'API', '接口', '服务', '微服务'
        ]
        
        for keyword in common_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        # 添加提取的技术关键词
        tech_terms = re.findall(r'\b[a-zA-Z]+[A-Z][a-zA-Z]+\b', text)
        keywords.extend(tech_terms)
        
        return list(set(keywords))
    
    def _select_design_pattern(self, keywords: List[str]) -> Dict:
        """选择设计模式"""
        # 关键词到模式的映射
        keyword_to_pattern = {
            '增删改查': 'crud',
            'CRUD': 'crud',
            '查询': 'crud',
            '用户界面': 'mvc',
            '界面': 'mvc',
            '数据访问': 'repository',
            '数据库': 'repository',
            '对象创建': 'factory',
            '创建对象': 'factory'
        }
        
        for keyword in keywords:
            if keyword in keyword_to_pattern:
                return self.design_patterns[keyword_to_pattern[keyword]]
        
        # 默认返回CRUD模式
        return self.design_patterns['crud']
    
    def _generate_components(self, pattern: Dict, context: Dict) -> List[Dict]:
        """生成组件列表"""
        components = []
        
        for comp_name in pattern['components']:
            # 查找是否有类似组件可以复用
            similar_component = self._find_similar_component(comp_name, context)
            
            if similar_component:
                components.append({
                    'name': comp_name,
                    'responsibility': f'负责{comp_name.lower()}相关逻辑',
                    'implementation': f'可复用现有组件：{similar_component}',
                    'status': 'reuse'
                })
            else:
                components.append({
                    'name': comp_name,
                    'responsibility': f'负责{comp_name.lower()}相关逻辑',
                    'implementation': '需要新开发',
                    'status': 'new'
                })
        
        return components
    
    def _find_similar_component(self, comp_name: str, context: Dict) -> Optional[str]:
        """查找类似组件"""
        existing_files = context.get('files', [])
        
        comp_lower = comp_name.lower()
        
        for file in existing_files[:10]:  # 只检查前10个文件
            if comp_lower in file.lower():
                return file
            
            # 检查常见变体
            if comp_name == 'Controller' and 'handler' in file.lower():
                return file
            elif comp_name == 'Repository' and 'dao' in file.lower():
                return file
            elif comp_name == 'Service' and 'manager' in file.lower():
                return file
        
        return None
    
    def _generate_steps(self, pattern: Dict, context: Dict) -> List[str]:
        """生成实施步骤"""
        steps = [
            f"1. 分析现有代码结构，确定{pattern['name']}模式的适配点",
            f"2. 设计{pattern['name']}模式的组件接口",
            f"3. 实现{pattern['name']}模式的核心组件",
            "4. 编写单元测试确保功能正确性",
            "5. 集成到现有系统并进行端到端测试",
            "6. 编写使用文档和API文档"
        ]
        
        return steps
    
    def _find_integration_points(self, context: Dict) -> List[str]:
        """查找集成点"""
        integration_points = []
        
        existing_files = context.get('files', [])
        
        # 常见的集成点
        common_integration = ['用户认证系统', '日志系统', '配置管理', '数据库连接']
        
        # 根据现有文件添加具体集成点
        for file in existing_files[:5]:
            if 'auth' in file.lower():
                integration_points.append(f'与认证系统集成（参考：{file}）')
            elif 'log' in file.lower():
                integration_points.append(f'与日志系统集成（参考：{file}）')
            elif 'config' in file.lower():
                integration_points.append(f'与配置管理系统集成（参考：{file}）')
        
        # 添加通用集成点
        integration_points.extend([
            '与现有的数据模型集成',
            '与业务逻辑层集成',
            '与API接口层集成'
        ])
        
        return integration_points[:5]  # 返回前5个

if __name__ == "__main__":
    # 初始化生成器
    design_generator = DesignSolutionGenerator()
    code_function_path = "../data/analyze_function.json"
    code_files = json.load(open(code_function_path, 'r'))
    # 示例需求
    context = {
        'files': [f['file_path'] for f in code_files],
        'languages': list(set(f['language'] for f in code_files))
    }
        
    sample_requirements = [
        "为系统添加实时通知功能",
        "需要添加用户管理功能，支持增删改查",
        "要实现文件上传和下载功能",
        "需要优化系统的查询性能"
    ]
    design_solutions = []
    for req in sample_requirements:
        solution = design_generator.generate_for_requirement(req, context)
        design_solutions.append(solution)
    
    design_solution_file = "../data/design_solution.json"
    with open(design_solution_file, 'w', encoding='utf-8') as f:
        json.dump(design_solutions, f, ensure_ascii=False, indent=2)
        
