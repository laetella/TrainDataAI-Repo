from typing import List, Dict, Any, Tuple, Optional
import re
import json

class DesignSolutionGenerator:
    """设计方案生成器"""
    
    def __init__(self):
        self.reasoning_trace = [] 
        self.design_patterns = {
            'event_driven': {
                'name': '事件驱动架构',
                'components': ['Event Producer', 'Message Broker', 'Event Consumer', 'Saga Orchestrator'],
                'description': '通过事件解耦微服务，支持高并发处理',
                'tech_stack': ['Kafka', 'RabbitMQ'],
                'rationale': """选择依据：
                - 高并发场景下，事件驱动架构通过异步处理和水平扩展实现线性吞吐量提升
                - Kafka的分区机制和批处理能力特别适合订单处理场景
                - Saga模式解决分布式事务问题，保证最终一致性""",
                'tradeoffs': """权衡考虑：
                - 增加系统复杂性（需要引入事件路由和状态管理）
                - 需要建立监控体系保证事件可靠性
                - 开发成本高于传统CRUD模式"""
            },
            'crud': {
                'name': 'CRUD操作',
                'components': ['Controller', 'Service', 'Repository', 'Model'],
                'description': '实现创建、读取、更新、删除操作的标准模式, 标准增删改查操作模式',
                'tech_stack': ['Spring Data', 'MyBatis'],
                'rationale': """选择依据：
                - 简单直观适合数据管理场景，中小型项目快速迭代
                - Spring Data自动生成CRUD接口，MyBatis灵活SQL映射提升开发效率
                - 适合数据密集型应用，如内容管理系统""",
                'tradeoffs': """权衡考虑：
                - 业务逻辑与数据访问强耦合，扩展性受限
                - 高并发场景易出现数据库瓶颈
                - 缺乏分布式事务支持，跨服务操作需额外方案"""
            },
            'two_pc': {
                'name': '两阶段提交',
                'components': ['Transaction Coordinator', 'Participant Services', 'Undo Log'],
                'description': '分布式事务解决方案，保证强一致性',
                'tech_stack': ['Seata', 'Atomikos'],
                'rationale': """选择依据：
                - 金融交易等强一致性场景刚需，确保原子操作
                - Seata提供全局事务管理，Atomikos支持多数据源事务
                - 协调器管理事务状态，参与者通过Undo Log实现回滚""",
                'tradeoffs': """权衡考虑：
                - 同步阻塞导致性能损耗，高并发场景吞吐量下降
                - 协调器单点故障风险，需设计高可用方案
                - 复杂事务场景协调成本高，调试困难"""
            },
            'microservices': {
                'name': '微服务架构',
                'components': ['API Gateway', 'Service Mesh', 'Config Server', 'Circuit Breaker'],
                'description': '服务拆分与治理架构',
                'tech_stack': ['Spring Cloud', 'Istio'],
                'rationale': """选择依据：
                - 服务独立部署扩展，提升系统弹性与容错能力
                - Spring Cloud提供服务发现/配置中心/熔断等组件
                - Istio实现服务网格层治理，支持无侵入式流量管理""",
                'tradeoffs': """权衡考虑：
                - 服务治理复杂度激增，需监控/追踪/日志体系支撑
                - 网络调用延迟增加，分布式事务成本高
                - 团队技术栈多样化带来维护成本上升"""
            },
            'mvc': {
                'name': 'MVC模式',
                'components': ['Model', 'View', 'Controller'],
                'description': '分离数据模型、用户界面和控制逻辑',
                'tech_stack': ['Spring MVC', 'Django', 'Rails'],
                'rationale': """选择依据：
                - 关注点分离提升代码可维护性，前后端解耦
                - Spring MVC支持RESTful开发，Django内置ORM模板引擎
                - 框架路由机制加速Web应用开发，适合快速迭代""",
                'tradeoffs': """权衡考虑：
                - 分层架构在小型项目中可能过度设计
                - 视图层与模型层耦合风险，需注意职责划分
                - 大型项目中控制器可能膨胀，需模块化拆分"""
            },
            'repository': {
                'name': '仓储模式',
                'components': ['Repository', 'Entity', 'DataContext'],
                'description': '数据访问层封装模式, 封装数据访问逻辑，提供统一的数据操作接口',
                'tech_stack': ['Entity Framework', 'Hibernate', 'SQLAlchemy'],
                'rationale': """选择依据：
                - 抽象数据访问细节，便于切换数据库类型
                - 支持单元测试与依赖注入，提升代码质量
                - 统一接口规范，降低业务层与数据层的耦合""",
                'tradeoffs': """权衡考虑：
                - 额外抽象层可能影响性能，需权衡ORM效率
                - 数据映射配置复杂度随实体增多而上升
                - 需维护数据上下文生命周期，避免内存泄漏"""
            },
            'factory': {
                'name': '工厂模式',
                'components': ['Factory', 'Product', 'ConcreteProduct'],
                'description': '通过工厂类创建对象，隐藏对象创建细节',
                'tech_stack': ['Java Factory Pattern', 'C# Factory Method'],
                'rationale': """选择依据：
                - 对象创建逻辑与使用分离，支持多态扩展
                - 适合对象类型动态变化的场景（如策略模式）
                - 提升代码灵活性，便于后续功能扩展""",
                'tradeoffs': """权衡考虑：
                - 增加类文件数量，可能复杂化项目结构
                - 过度使用易导致过度设计，需评估实际需求
                - 工厂方法调用链可能增加运行时开销"""
            }
        }

    def analyze_requirements(self, requirement_text):
        """需求分析 - 提取技术关键词和架构需求"""
        keywords = self._extract_keywords(requirement_text)
        # 识别高并发相关关键词
        concurrency_keywords = ['高并发', 'QPS', 'TPS', '分布式事务', '强一致性']
        arch_requirements = []
        for kw in concurrency_keywords:
            if kw in requirement_text:
                arch_requirements.append(kw)
        return {
            'functional': [kw for kw in keywords if not kw.startswith('#')],
            'architectural': arch_requirements
        }
    
    def generate_design(self, context):
        """生成完整设计方案"""
        self.reasoning_trace = []

        # 推理步骤1：需求分析
        requirement = context['requirement']
        self._trace("分析需求文本", f"需求原文：'{requirement}'")
        analysis = self.analyze_requirements(requirement)
        self._trace("关键词提取", f"提取到功能关键词：{analysis['functional']}")
        self._trace("架构需求识别", f"识别到架构需求：{analysis['architectural']}")
        
        # 推理步骤2：模式选择
        pattern_key = self._select_design_pattern(analysis)
        pattern = self.design_patterns[pattern_key]
        self._trace("模式选择", f"根据架构需求选择模式：{pattern['name']}")
        self._trace("选择依据", f"因为需求包含{analysis['architectural']}，选择{pattern_key}模式")
        
        # 推理步骤3：组件生成
        self._trace("组件生成", f"为模式{pattern['name']}生成实现组件")
        components = self._generate_components(pattern, context)
        
        # 推理步骤4：实施步骤
        self._trace("实施规划", f"为{pattern['name']}模式规划实施步骤")
        steps = self._generate_steps(pattern, context)
        
        # 推理步骤5：性能优化
        self._trace("性能优化", f"为{pattern['name']}生成性能优化策略")
        perf_cons = self._generate_performance_considerations(pattern)
        
        solution = {
            'requirement': requirement,
            'design_pattern': pattern['name'],
            'description': pattern['description'],
            'components': components,
            'implementation_steps': steps,
            'tech_stack': pattern['tech_stack'],
            'integration_points': self._find_integration_points(context),
            'performance_considerations': perf_cons,
            'reasoning_trace': self.reasoning_trace  # 包含完整推理路径
        }
        return solution
    
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
    
    def _trace(self, step_name: str, details: str):
        """记录推理步骤"""
        self.reasoning_trace.append({
            'step': step_name,
            'details': details,
            'timestamp': self._get_timestamp()
        })

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _generate_performance_considerations(self, pattern: Dict) -> Dict:
        """生成性能优化建议"""
        recommendations = {}
        if pattern['name'] == '事件驱动架构':
            recommendations = {
                'throughput_optimization': '使用Kafka分区策略实现水平扩展',
                'latency_optimization': '消费者组批处理配置（batch.size=1000）',
                'monitoring': 'Prometheus+Grafana监控端到端延迟'
            }
        elif pattern['name'] == '两阶段提交':
            recommendations = {
                'transaction_timeout': '配置全局事务超时（默认90s）',
                'retry_strategy': '指数退避重试机制',
                'undo_log_cleanup': '定时任务清理过期undo日志'
            }
        return recommendations

    def _extract_keywords(self, requirement) -> List[str]:
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
        requirement = str(requirement)
        for keyword in common_keywords:
            if keyword in requirement:
                keywords.append(keyword)
        
        # 添加架构相关关键词
        # print("text: ", requirement)
        arch_keywords = ['高并发', 'QPS', 'TPS', '分布式事务', '强一致性', '最终一致性']
        for kw in arch_keywords:
            re.search(r'\b' + re.escape(kw) + r'\b', requirement)
            keywords.append(f'#{kw}')
        
        # 提取技术术语
        tech_terms = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]{2,}\b', requirement)
        keywords.extend([t for t in tech_terms if len(t) > 2])
        # print("keywords : ", keywords)
        return list(set(keywords))
    
    def _select_design_pattern(self, analysis: Dict) -> str:
        """带推理trace的模式选择"""
        # 默认模式
        pattern_key = 'crud'
        
        # 高并发场景推理
        if '高并发' in analysis['architectural']:
            self._trace("模式选择推理", "检测到高并发需求，考虑事件驱动架构")
            pattern_key = 'event_driven'
            
        # 分布式事务推理
        if '分布式事务' in analysis['architectural'] or '强一致性' in analysis['architectural']:
            self._trace("模式选择推理", "检测到强一致性需求，考虑两阶段提交模式")
            pattern_key = 'two_pc'
            
        # 微服务推理
        if '服务拆分' in analysis['functional'] or '微服务' in analysis['functional']:
            self._trace("模式选择推理", "检测到服务拆分需求，考虑微服务架构")
            pattern_key = 'microservices'
            
        self._trace("最终模式选择", f"确定使用{pattern_key}模式")
        return pattern_key
    
    def _generate_components(self, pattern: Dict, context: Dict) -> List[Dict]:
        """生成组件列表"""
        components = []
        tech_stack = pattern.get('tech_stack', [])
        for comp_name in pattern['components']:
            # 查找是否有类似组件可以复用
            similar_component = self._find_similar_component(comp_name, context)
            implementation_detail = f"使用{tech_stack[0] if tech_stack else '标准实现'}"
            if similar_component:
                components.append({
                    'name': comp_name,
                    'responsibility': f'负责{comp_name.lower()}相关逻辑',
                    'implementation': implementation_detail,
                    'status': 'reuse'
                })
            else:
                components.append({
                    'name': comp_name,
                    'responsibility': f'负责{comp_name.lower()}相关逻辑',
                    'implementation': implementation_detail,
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
        steps = []
        pattern_name = pattern['name']
        
        if pattern_name == '事件驱动架构':
            steps = [
                "1. 配置Kafka集群作为消息中间件",
                "2. 实现订单创建事件生产者（Spring Cloud Stream）",
                "3. 开发订单状态变更消费者（KafkaListener）",
                "4. 配置Saga编排器处理分布式事务",
                "5. 集成Prometheus监控端到端性能指标"
            ]
        elif pattern_name == '两阶段提交':
            steps = [
                "1. 配置Seata TC服务端",
                "2. 在支付服务中添加全局事务注解",
                "3. 实现undo_log表持久化逻辑",
                "4. 配置事务超时和重试策略",
                "5. 开发事务协调器管理界面"
            ]
        else:
            steps = [
                f"1. 分析现有代码结构，确定{pattern_name}模式的适配点",
                f"2. 设计{pattern_name}模式的组件接口",
                f"3. 实现{pattern_name}模式的核心组件",
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
        # 识别现有系统组件
        existing_components = {}
        for file in existing_files:
            if 'auth' in file.lower():
                existing_components['auth'] = file
            elif 'log' in file.lower():
                existing_components['log'] = file
            elif 'config' in file.lower():
                existing_components['config'] = file
            elif 'gateway' in file.lower():
                existing_components['gateway'] = file
        
        # 根据架构模式推荐集成点
        if existing_components:
            if 'gateway' in existing_components:
                integration_points.append(f'与API网关集成（参考：{existing_components["gateway"]}）')
            if 'auth' in existing_components:
                integration_points.append(f'与认证系统集成（参考：{existing_components["auth"]}）')
            if 'log' in existing_components:
                integration_points.append(f'与日志系统集成（参考：{existing_components["log"]}）')
            if 'config' in file.lower():
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
        'languages': list(set(f['language'] for f in code_files)),
        'requirement': [
        "为系统添加实时通知功能",
        "实现高并发订单处理系统，支持每秒1000+订单创建，要求数据强一致",
        "需要添加用户管理功能，支持增删改查",
        "要实现文件上传和下载功能",
        "需要优化系统的查询性能"
        ]
    }
    
    design_solutions = design_generator.generate_design(context)
    
    design_solution_file = "../data/design_solution.json"
    with open(design_solution_file, 'w', encoding='utf-8') as f:
        json.dump(design_solutions, f, ensure_ascii=False, indent=2)
        
