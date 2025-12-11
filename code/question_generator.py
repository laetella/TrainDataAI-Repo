import ast
import os
import re
import json
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
import random
from pycparser import c_parser, c_ast
from datetime import datetime

class ReasoningGenerator:
    """推理过程生成器"""
    
    def __init__(self):
        self.reasoning_templates = {
            'function_purpose': {
                # "这个{function_name}函数是做什么的？": {
                    "steps": [
                        "分析函数名称和命名规范，从中提取功能线索",
                        "检查函数参数列表，推断输入输出关系",
                        "查看函数体中的关键操作和返回值",
                        "查找函数文档字符串或注释（如果有）",
                        "分析函数在代码库中的调用位置和上下文",
                        "综合以上信息总结函数的主要功能和目的"
                    ],
                    "example_answer": "通过分析函数名'{function_name}'，结合参数类型和函数体中的主要操作，可以推断该函数主要用于{purpose}",
                    "reasoning_trace": "步骤1：函数名称包含'{keyword}'，通常表示{explain}\n步骤2：参数包括{params}，表明需要处理{data_types}\n步骤3：函数体内有{operation}操作，返回{return_value}\n步骤4：总结功能为{purpose}"
                # }
            },
            'parameter_usage': {
                # "{function_name}函数的{param}参数有什么作用？": {
                    "steps": [
                        "检查参数{param}在函数签名中的位置和类型注解",
                        "查看函数体内对参数{param}的所有使用位置",
                        "分析参数{param}如何影响函数的逻辑流程",
                        "检查是否有对参数{param}的验证或转换逻辑",
                        "查看其他调用该函数时传递的参数{param}的示例",
                        "总结参数{param}的作用、约束和使用建议"
                    ],
                    'example_answer': "参数'{param}'主要用于{purpose}，它{additional_info}。",
                    "reasoning_trace": "1. 参数类型：{param_type}\n2. 在函数中的使用：{usage_context}\n3. 验证逻辑：{validation_logic}\n4. 影响结果：{impact_on_result}\n5. 使用建议：{usage_suggestion}"
                # }
            },
            'usage_example': {
                'steps': [
                    "分析函数的输入参数要求",
                    "确定每个参数的数据类型和约束",
                    "构造典型的调用场景",
                    "考虑边界条件和异常处理",
                    "提供完整的调用示例"
                ],
                'example_answer': "正确的调用方式需要提供合适的参数值，确保函数功能正常执行。"
            },
            'code_logic': {
                # "这段代码中的 {keyword} 有什么作用？": {
                    "steps": [
                        "定位代码中{keyword}的出现位置",
                        "分析{keyword}的语法角色（变量、函数、关键字等）",
                        "查看{keyword}的定义和初始化过程",
                        "跟踪{keyword}在代码流程中的变化和使用",
                        "分析{keyword}对整个算法或逻辑的贡献",
                        "评估如果没有{keyword}，代码行为会有何不同"
                    ],
                    "reasoning_trace": "定位：在第{line}行发现{keyword}\n角色：{syntactic_role}\n定义：{definition_info}\n使用：在{usage_context}中使用\n影响：对{affected_aspect}有重要影响\n替代：可以用{alternative}替代但会{consequence}"
                # }
            },
            'error_handling': {
                # "如果输入为空值会发生什么？": {
                    "steps": [
                        "检查代码中是否包含对空值的显式检查",
                        "分析如果没有空值检查，代码执行路径会如何变化",
                        "查看相关的异常处理机制",
                        "评估空值输入对后续处理的影响",
                        "检查是否有默认值或回退逻辑",
                        "总结空值处理的完整流程和潜在风险"
                    ],
                    "reasoning_trace": "检查点：{check_points}\n异常处理：{exception_handling}\n默认行为：{default_behavior}\n影响范围：{impact_scope}\n改进建议：{improvement_suggestion}"
                # }
            },
            'optimization': {
                # "这段代码在性能上有哪些优化空间？": {
                    "steps": [
                        "分析代码的时间复杂度",
                        "检查内存使用情况",
                        "识别可能的瓶颈（如循环嵌套、重复计算）",
                        "查看是否有缓存机制可以引入",
                        "评估算法是否可以优化",
                        "检查是否有不必要的I/O操作",
                        "提出具体的优化建议"
                    ],
                    "reasoning_trace": "时间复杂度：{time_complexity}\n内存占用：{memory_usage}\n瓶颈识别：{bottleneck}\n优化建议：{optimization_suggestions}\n预期改进：{expected_improvement}"
                # }
            }
        }
    
    def generate_reasoning_trace(self, question_type: str, question: str, context: Dict) -> Dict:
        """为问题生成推理过程"""
        
        # 提取问题中的变量
        variables = self._extract_variables(question)
        
        # 获取对应的推理模板
        if question_type in self.reasoning_templates:
            templates = self.reasoning_templates[question_type]
            
            # 找到最匹配的模板
            matched_template = None
            for template_question, template_data in templates.items():
                # 简单模式匹配
                if self._is_template_match(template_question, question):
                    matched_template = template_data
                    break
            
            if matched_template:
                # 填充模板
                reasoning_steps = matched_template["steps"]
                reasoning_trace = self._fill_template(
                    matched_template.get("reasoning_trace", ""),
                    variables,
                    context
                )
                
                return {
                    "question": question,
                    "question_type": question_type,
                    "reasoning_steps": reasoning_steps,
                    "reasoning_trace": reasoning_trace,
                    "answer_generation_process": self._generate_answer_process(question_type, context)
                }
        
        # 默认推理过程
        return self._generate_default_reasoning(question, context)
    
    def generate_for_function_purpose(self, func_info: Dict, code_context: Dict) -> Dict:
        """为函数目的问题生成推理过程"""
        func_name = func_info.get('name', '未知函数')
        params = func_info.get('params', [])
        purpose = self._guess_function_purpose(func_name)
        
        # 生成推理步骤
        steps = []
        for step_template in self.reasoning_templates['function_purpose']['steps']:
            step = step_template.format(
                function_name=func_name,
                params=params,
                purpose=purpose
            )
            steps.append(step)
        
        # 生成结论
        example_answer = self.reasoning_templates['function_purpose']['example_answer'].format(
            function_name=func_name,
            purpose=purpose,
            param_count=len(params)
        )
        
        return {
            'reasoning_type': 'function_purpose',
            'reasoning_steps': steps,
            'example_answer': example_answer,
            'reasoning_chain': self._build_reasoning_chain(steps, example_answer, code_context)
        }
    
    def generate_for_parameter_usage(self, func_info: Dict, param: str, code_context: Dict) -> Dict:
        """为参数使用问题生成推理过程"""
        func_name = func_info.get('name', '未知函数')
        param_purpose = self._guess_param_purpose(param)
        
        # 检查参数是否在函数参数列表中
        params = func_info.get('params', [])
        param_exists = param in params
        
        # 生成推理步骤
        steps = []
        for step_template in self.reasoning_templates['parameter_usage']['steps']:
            step = step_template.format(
                param=param,
                function_name=func_name,
                exists="是函数的输入参数" if param_exists else "可能不是函数的直接参数"
            )
            steps.append(step)
        
        # 生成结论
        example_answer = self.reasoning_templates['parameter_usage']['example_answer'].format(
            param=param,
            purpose=param_purpose,
            additional_info="影响着函数的业务逻辑" if param_exists else "需要根据实际使用场景判断"
        )
        
        return {
            'reasoning_type': 'parameter_usage',
            'reasoning_steps': steps,
            'example_answer': example_answer,
            'reasoning_chain': self._build_reasoning_chain(steps, example_answer, code_context)
        }
    
    def generate_for_usage_example(self, func_info: Dict, code_context: Dict) -> Dict:
        """为使用示例问题生成推理过程"""
        func_name = func_info.get('name', '未知函数')
        params = func_info.get('params', [])
        
        # 生成推理步骤
        steps = []
        for step_template in self.reasoning_templates['usage_example']['steps']:
            step = step_template.format(
                function_name=func_name,
                param_count=len(params)
            )
            steps.append(step)
        
        example_answer = self.reasoning_templates['usage_example']['example_answer']
        
        return {
            'reasoning_type': 'usage_example',
            'reasoning_steps': steps,
            'example_answer': example_answer,
            'reasoning_chain': self._build_reasoning_chain(steps, example_answer, code_context)
        }
    
    def _extract_variables(self, question: str) -> Dict:
        """从问题中提取变量"""
        variables = {}
        
        # 提取函数名
        func_match = re.search(r'\{function_name\}', question)
        if func_match:
            # 在实际使用中，这里应该从上下文获取真实的函数名
            variables["function_name"] = "example_function"
        
        # 提取参数名
        param_match = re.search(r'\{param\}', question)
        if param_match:
            variables["param"] = "input_param"
        
        # 提取关键词
        keyword_match = re.search(r'\{keyword\}', question)
        if keyword_match:
            variables["keyword"] = "important_keyword"
        
        return variables
    
    def _is_template_match(self, template: str, question: str) -> bool:
        """检查问题是否匹配模板"""
        # 将模板转换为正则表达式
        pattern = template.replace('{', r'(.+)').replace('}', r'')
        return re.match(pattern, question) is not None
    
    def _fill_template(self, template: str, variables: Dict, context: Dict) -> str:
        """填充模板"""
        result = template
        
        # 用变量替换占位符
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, value)
        
        # 用上下文信息填充其他占位符
        if "{keyword}" in result and "keyword" in context:
            result = result.replace("{keyword}", context["keyword"])
        
        if "{params}" in result and "params" in context:
            result = result.replace("{params}", str(context["params"]))
        
        # 其他通用替换
        replacements = {
            "{explain}": "解释性说明",
            "{data_types}": "特定类型的数据",
            "{operation}": "关键操作",
            "{return_value}": "处理结果",
            "{purpose}": "核心功能",
            "{param_type}": "字符串/整数等类型",
            "{usage_context}": "处理流程中的特定环节",
            "{validation_logic}": "类型检查或范围验证",
            "{impact_on_result}": "直接影响输出",
            "{usage_suggestion}": "传递有效值的建议",
            "{line}": "具体行号",
            "{syntactic_role}": "循环控制/条件判断等",
            "{definition_info}": "初始化和赋值情况",
            "{affected_aspect}": "算法效率或正确性",
            "{alternative}": "其他实现方式",
            "{consequence}": "降低性能或增加复杂度",
            "{check_points}": "输入验证的位置",
            "{exception_handling}": "抛出异常或记录日志",
            "{default_behavior}": "返回默认值或空结果",
            "{impact_scope}": "影响的范围大小",
            "{improvement_suggestion}": "增加空值检查或提供默认值",
            "{time_complexity}": "O(n)或其他复杂度",
            "{memory_usage}": "空间消耗情况",
            "{bottleneck}": "主要性能瓶颈",
            "{optimization_suggestions}": "具体优化方案",
            "{expected_improvement}": "性能提升预期"
        }
        
        for placeholder, default_value in replacements.items():
            if placeholder in result:
                result = result.replace(placeholder, default_value)
        
        return result
    
    def _generate_answer_process(self, question_type: str, context: Dict) -> str:
        """生成答案生成过程"""
        
        processes = {
            'function_purpose': [
                "1. 解析函数签名，提取基本信息",
                "2. 分析函数体中的主要操作序列",
                "3. 检查返回值类型和意义",
                "4. 查看调用关系，了解使用场景",
                "5. 综合所有信息形成功能描述"
            ],
            'parameter_usage': [
                "1. 定位参数在函数中的声明位置",
                "2. 追踪参数在函数体内的所有引用",
                "3. 分析参数如何参与计算和逻辑判断",
                "4. 检查参数约束和边界条件",
                "5. 总结参数的作用和使用方法"
            ],
            'code_logic': [
                "1. 理解代码段的整体结构和目的",
                "2. 分析特定元素在结构中的角色",
                "3. 跟踪数据流和控制流",
                "4. 识别关键逻辑决策点",
                "5. 解释元素对整体逻辑的贡献"
            ],
            'error_handling': [
                "1. 识别代码中的异常处理机制",
                "2. 分析各种输入条件下的行为",
                "3. 检查错误传播路径",
                "4. 评估错误处理的有效性",
                "5. 描述异常情况的处理流程"
            ],
            'optimization': [
                "1. 测量或估计当前性能指标",
                "2. 识别性能热点和瓶颈",
                "3. 分析算法复杂度和资源使用",
                "4. 提出具体的优化策略",
                "5. 评估优化效果和权衡"
            ]
        }
        
        return processes.get(question_type, [
            "1. 理解问题意图",
            "2. 分析相关代码",
            "3. 提取关键信息",
            "4. 构建逻辑解释",
            "5. 验证解释正确性"
        ])
    
    def _generate_default_reasoning(self, question: str, context: Dict) -> Dict:
        """生成默认推理过程"""
        return {
            "question": question,
            "question_type": "general",
            "reasoning_steps": [
                "理解问题的核心关注点",
                "定位代码中的相关信息",
                "分析代码逻辑和结构",
                "提取关键要素和关系",
                "构建逻辑解释和答案"
            ],
            "reasoning_trace": f"针对问题'{question}'的推理过程：\n1. 分析问题意图：理解用户想要了解{question}背后的代码逻辑\n2. 代码分析：检查相关代码段，识别关键结构和元素\n3. 逻辑推理：基于代码分析，推导出问题的答案\n4. 验证：确认推理结果与代码实际行为一致",
            "answer_generation_process": [
                "解析问题并确定分析重点",
                "定位相关代码片段",
                "深入分析代码逻辑",
                "构建逻辑解释链",
                "形成最终答案"
            ]
        }
    
    def _guess_function_purpose(self, func_name: str) -> str:
        """根据函数名猜测功能"""
        patterns = {
            r'.*[Gg]et.*': '获取数据',
            r'.*[Ss]et.*': '设置数据',
            r'.*[Cc]reate.*': '创建对象',
            r'.*[Uu]pdate.*': '更新数据',
            r'.*[Dd]elete.*': '删除数据',
            r'.*[Cc]alculate.*': '计算数值',
            r'.*[Ff]ormat.*': '格式化输出',
            r'.*[Pp]arse.*': '解析数据',
            r'.*[Hh]andle.*': '处理请求',
            r'.*[Ss]end.*': '发送数据',
            r'.*[Rr]eceive.*': '接收数据',
            r'.*[Vv]alidate.*': '验证输入',
            r'.*[Ii]nit.*': '初始化',
            r'.*[Ss]tart.*': '启动过程',
            r'.*[Ss]top.*': '停止过程'
        }
        
        func_name_lower = func_name.lower()
        for pattern, purpose in patterns.items():
            if re.match(pattern, func_name_lower):
                return purpose
        
        return "执行特定业务逻辑"
    
    def _guess_param_purpose(self, param: str) -> str:
        """猜测参数用途"""
        param_lower = param.lower()
        
        purpose_map = {
            'user': '标识用户身份或获取用户信息',
            'id': '作为唯一标识符',
            'name': '表示名称或标题信息',
            'data': '包含需要处理的数据内容',
            'file': '指定文件路径或文件对象',
            'path': '表示文件系统路径',
            'config': '提供配置参数',
            'options': '传递选项参数',
            'callback': '用于回调函数',
            'timeout': '设置超时时间',
            'count': '指定数量限制',
            'limit': '设置限制条件',
            'offset': '指定偏移量',
            'query': '包含查询条件',
            'filter': '用于数据过滤',
            'sort': '指定排序方式'
        }
        
        for key, purpose in purpose_map.items():
            if key in param_lower:
                return purpose
        
        return "传递必要的数据参数"
    
    def _build_reasoning_chain(self, steps: List[str], example_answer: str, code_context: Dict) -> str:
        """构建完整的推理链条"""
        chain = "推理过程分析：\n\n"
        
        # 添加代码上下文信息
        if code_context.get('context_type') != 'missing':
            chain += "代码上下文：\n"
            chain += f"文件：{code_context.get('file', '未知')}\n"
            chain += f"行号：{code_context.get('function_line', '未知')}\n\n"
        
        # 添加推理步骤
        chain += "推理步骤：\n"
        for i, step in enumerate(steps, 1):
            chain += f"{i}. {step}\n"
        
        # 添加结论
        chain += f"\n推理结论：{example_answer}"
        
        return chain


class QAPairGenerator:
    """问答对生成器"""
    
    def __init__(self):
        self.reasoning_generator = ReasoningGenerator()
        self.qa_templates = {
            'function_purpose': [
                "这个{function_name}函数是做什么的？",
                "请解释{function_name}函数的功能",
                "{function_name}函数的主要作用是什么？",
                "这个{function_name}函数解决了什么问题？"
            ],
            'parameter_usage': [
                "{function_name}函数的{param}参数有什么作用？",
                "如何使用{function_name}函数的{param}参数？",
                "参数 {param} 的取值范围是什么？"
            ],
            'code_logic': [
                "这段代码中的 {keyword} 有什么作用？",
                "循环结构在这里的作用是什么？",
                "条件判断的逻辑是怎样的？"
            ],
            'error_handling': [
                "如果输入为空值会发生什么？",
                "这段代码如何处理异常情况？",
                "当输入非法参数时会有哪些表现？"
            ],
            'optimization': [
                "这段代码在性能上有哪些优化空间？",
                "如何减少这段代码的内存占用？",
                "是否有更简洁的实现方式？"
            ],
            'usage_example': [
                "如何调用{function_name}函数？",
                "请给出{function_name}函数的调用示例"
            ],
            'business_logic': [
                "这段代码实现了什么业务逻辑？",
                "这个模块处理什么业务流程？"
            ]
        }
        
    def generate_from_function(self, func: Dict) -> List[Dict]:
        """从函数生成问答对"""
        qa_pairs = []
        func_name = func.get('name', '')
        params = func.get('params', [])
        code_context = dict()
        code_context['function'] =  func_name
        
        code_context['parameter']= params
        
        # 1. 函数目的问答
        qa_list = self._generate_function_purpose_answer(func, code_context)
        qa_pairs.extend(qa_list)
           
        # 2. 参数相关问答 生成参数使用QA pairs（最多2个参数）
        for param in params:  
            qa_pairs.extend(self._generate_parameter_usage_qa(func, param, code_context))
        
        # 3. 生成使用示例QA pairs
        qa_pairs.extend(self._generate_usage_example_qa(func, code_context))
        
        for param in func.get('params', []):  
            for template in self.qa_templates['parameter_usage']:
                question = template.format(function_name=func_name, param=param)
                answer = f"参数'{param}'用于{self._guess_param_purpose(param, func)}"
                qa_pairs.append({
                    'question': question,
                    'answer': answer,
                    'type': 'parameter_usage',
                    'context': {'function': func_name, 'parameter': param},
                    'code_snippet': func.get('code_snippet', "null"),
                    'difficulty': 'medium'
                })
        
        # 3. 使用示例问答
        for template in self.qa_templates['usage_example']:
            question = template.format(function_name=func_name)
            answer = self._generate_usage_example(func)
            qa_pairs.append({
                'question': question,
                'answer': answer,
                'type': 'usage_example',
                'context': {'function': func_name},
                'code_snippet': func.get('code_snippet', "null"),
                'difficulty': 'medium'
            })
        # 代码逻辑问题
        if 'loop' in func.get('body', ''):
            qa_pairs.append({
                'question': self.qa_templates['code_logic'][1],
                'answer': "循环结构用于处理重复逻辑或遍历数据集合",
                'category': 'code_logic',
                'context': {'function': func_name},
                'code_snippet': func.get('code_snippet', "null"),
                'difficulty': 'medium'
            })
        
        # 错误处理问题
        qa_pairs.append({
            'question': random.choice(self.qa_templates['error_handling']),
            'answer': "需要添加输入验证和异常处理机制",
            'category': 'error_handling',
            'context': {'function': func_name},
            'code_snippet': func.get('code_snippet', "null"),
            'difficulty': 'hard'
        })
        
        # 优化建议问题
        if func.get('body', '').count('\n') > 10:
            qa_pairs.append({
                'question': random.choice(self.qa_templates['optimization']),
                'answer': "可以考虑使用更高效的数据结构或算法",
                'category': 'optimization',
                'context': {'function': func_name},
                'code_snippet': func.get('code_snippet', "null"),
                'difficulty': 'hard'
            })
        
        return qa_pairs
    
    def _generate_function_purpose_answer(self, func, code_context) -> str:
        """生成函数目的相关的QA pairs"""
        qa_list = []
        func_name = func.get('name', '未知函数')
        
        for template in self.qa_templates['function_purpose']:  # 最多2种问法
            question = template.format(function_name=func_name)
            
            # 生成答案
            answer = self._generate_function_answer(func)
            
            # 生成推理过程
            reasoning = self.reasoning_generator.generate_for_function_purpose(func, code_context)
            
            # 构建完整的QA pair
            qa_pair = {
                'question': question,
                'answer': answer,
                'type': 'function_purpose',
                'function': func_name,
                'file': func.get('file', '未知'),
                'language': func.get('language', '未知'),
                'code_context': code_context,
                'code_snippet': func.get('code_snippet', "null"),
                'reasoning': reasoning,
                'difficulty': 'easy',
                'generated_at': datetime.now().isoformat()
            }
            # print("qa_pair: ", qa_pair)
            # input()
            qa_list.append(qa_pair)
            # print("qa list size: ", len(qa_list))
        return qa_list
    
    def _generate_parameter_usage_qa(self, func_info: Dict, param: str, code_context: Dict) -> List[Dict]:
        """生成参数使用相关的QA pairs"""
        qa_list = []
        func_name = func_info.get('name', '未知函数')
        
        for template in self.qa_templates['parameter_usage'][:1]:  # 每种参数1种问法
            question = template.format(function_name=func_name, param=param)
            
            # 生成答案
            answer = self._generate_param_answer(func_info, param)
            
            # 生成推理过程
            reasoning = self.reasoning_generator.generate_for_parameter_usage(func_info, param, code_context)
            
            # 构建完整的QA pair
            qa_pair = {
                'question': question,
                'answer': answer,
                'type': 'parameter_usage',
                'function': func_name,
                'parameter': param,
                'file': func_info.get('file', '未知'),
                'language': func_info.get('language', '未知'),
                'code_context': code_context,
                'code_snippet': func_info.get('code_snippet', "null"),
                'reasoning': reasoning,
                'difficulty': 'medium',
                'generated_at': datetime.now().isoformat()
            }
            
            qa_list.append(qa_pair)
        
        return qa_list
    
    def _generate_usage_example_qa(self, func_info: Dict, code_context: Dict) -> List[Dict]:
        """生成使用示例相关的QA pairs"""
        qa_list = []
        func_name = func_info.get('name', '未知函数')
        
        for template in self.qa_templates['usage_example'][:1]:  # 1种问法
            question = template.format(function_name=func_name)
            
            # 生成答案
            answer = self._generate_usage_example_answer(func_info)
            
            # 生成推理过程
            reasoning = self.reasoning_generator.generate_for_usage_example(func_info, code_context)
            
            # 构建完整的QA pair
            qa_pair = {
                'question': question,
                'answer': answer,
                'type': 'usage_example',
                'function': func_name,
                'file': func_info.get('file', '未知'),
                'language': func_info.get('language', '未知'),
                'code_context': code_context,
                'code_snippet': func_info.get('code_snippet', "null"),
                'reasoning': reasoning,
                'difficulty': 'medium',
                'generated_at': datetime.now().isoformat()
            }
            
            qa_list.append(qa_pair)
        
        return qa_list
    
    def _generate_function_answer(self, func_info: Dict) -> str:
        """生成函数功能答案"""
        func_name = func_info.get('name', '未知函数')
        params = func_info.get('params', [])
        docstring = func_info.get('docstring')
        
        # 根据函数名猜测功能
        purpose = self.reasoning_generator._guess_function_purpose(func_name)
        
        if docstring:
            return f"{func_name}函数主要用于{purpose}。\n\n文档说明：{docstring[:150]}{'...' if len(docstring) > 150 else ''}"
        else:
            param_info = f"接收{len(params)}个参数" if params else "无参数"
            return f"{func_name}函数{param_info}，主要用于{purpose}。"
    
    def _generate_param_answer(self, func_info: Dict, param: str) -> str:
        """生成参数作用答案"""
        func_name = func_info.get('name', '函数')
        param_purpose = self.reasoning_generator._guess_param_purpose(param)
        
        return f"在{func_name}函数中，参数'{param}'主要用于{param_purpose}。\n\n该参数影响着函数的输入处理逻辑。"
    
    def _generate_usage_example_answer(self, func_info: Dict) -> str:
        """生成使用示例答案"""
        func_name = func_info.get('name', '函数')
        params = func_info.get('params', [])
        
        # 生成示例参数值
        example_params = []
        param_descriptions = []
        
        for i, param in enumerate(params[:4]):  # 最多展示4个参数
            if 'id' in param.lower():
                example_params.append('"id_001"')
                param_descriptions.append(f"{param}: 标识符字符串")
            elif 'name' in param.lower():
                example_params.append('"example_name"')
                param_descriptions.append(f"{param}: 名称字符串")
            elif 'count' in param.lower() or 'limit' in param.lower():
                example_params.append('10')
                param_descriptions.append(f"{param}: 整数值")
            elif 'data' in param.lower():
                example_params.append('{"key": "value"}')
                param_descriptions.append(f"{param}: 数据对象")
            elif 'file' in param.lower():
                example_params.append('"path/to/file.txt"')
                param_descriptions.append(f"{param}: 文件路径")
            else:
                example_params.append(f'arg_{i+1}')
                param_descriptions.append(f"{param}: 输入参数")
        
        if len(params) > 4:
            example_params.append('...')
        
        example_call = f"{func_name}({', '.join(example_params)})"
        
        answer = f"调用示例：\n```\n{example_call}\n```\n\n"
        
        if param_descriptions:
            answer += "参数说明：\n"
            for desc in param_descriptions:
                answer += f"- {desc}\n"
        
        answer += "\n请根据实际需求传入合适的参数值。"
        
        return answer

    def _guess_function_purpose(self, func_name: str) -> str:
        """根据函数名猜测功能"""
        patterns = {
            r'.*[Gg]et.*': '获取数据',
            r'.*[Ss]et.*': '设置数据',
            r'.*[Cc]reate.*': '创建对象',
            r'.*[Uu]pdate.*': '更新数据',
            r'.*[Dd]elete.*': '删除数据',
            r'.*[Vv]alidate.*': '验证输入',
            r'.*[Cc]alculate.*': '计算数值',
            r'.*[Ff]ormat.*': '格式化输出',
            r'.*[Pp]arse.*': '解析数据',
            r'.*[Hh]andle.*': '处理请求',
            r'.*[Ss]end.*': '发送数据',
            r'.*[Rr]eceive.*': '接收数据'
        }
        
        for pattern, purpose in patterns.items():
            if re.match(pattern, func_name):
                return purpose
        
        return "处理特定业务逻辑"
    
    def _guess_param_purpose(self, param: str, func: Dict) -> str:
        """猜测参数用途"""
        param_lower = param.lower()
        
        purpose_map = {
            'user': '用户标识或信息',
            'id': '唯一标识符',
            'name': '名称或标题',
            'data': '数据内容',
            'file': '文件路径或对象',
            'path': '文件或路径',
            'config': '配置信息',
            'options': '选项参数',
            'callback': '回调函数',
            'timeout': '超时时间',
            'count': '数量',
            'limit': '限制数量',
            'offset': '偏移量',
            'query': '查询条件',
            'filter': '过滤条件',
            'sort': '排序方式'
        }
        
        for key, purpose in purpose_map.items():
            if key in param_lower:
                return purpose
        
        return "传入函数的数据"
    
    def _generate_usage_example(self, func: Dict) -> str:
        """生成使用示例"""
        func_name = func.get('name', '')
        params = func.get('params', [])
        
        # 生成示例参数值
        example_params = []
        for param in params[:3]:  # 只取前3个参数
            if 'id' in param.lower():
                example_params.append('"user_123"')
            elif 'name' in param.lower():
                example_params.append('"example_name"')
            elif 'count' in param.lower() or 'limit' in param.lower():
                example_params.append('10')
            elif 'data' in param.lower():
                example_params.append('{"key": "value"}')
            else:
                example_params.append('value')
        
        if len(params) > 3:
            example_params.append('...')
        
        example_call = f"{func_name}({', '.join(example_params)})"
        
        return f"调用示例：{example_call}。请根据实际需求传入合适的参数。"


# 集成使用示例
class TrainingDataGenerator:
    """训练数据生成器（整合版）"""

    def __init__(self):
        self.qa_generator = QAPairGenerator()
        self.reasoning_generator = ReasoningGenerator()
        
    def generate_from_codebase(self, codebase_path: str) -> Dict[str, Any]:
        """从代码库生成训练数据"""
        
        # 1. 收集代码信息
        code_files = json.load(open(codebase_path, 'r'))
        
        # 2. 生成问答对
        qa_pairs = []
        for code_file in code_files:
            # 从函数生成问答
            # print("code_file: ", code_file)
            # input()
            qa_pairs.extend(self.qa_generator.generate_from_function(code_file))
            
        print("generated %d qa_pairs! "%(len(qa_pairs)))
        
        # 4. 组装最终数据集
        dataset = {
            'metadata': {
                'source': codebase_path,
                'total_qa_pairs': len(qa_pairs),
                'generated_at': datetime.now().isoformat()
            },
            'qa_pairs': qa_pairs, # [:50],  # 限制数量，防止过大
        }
        
        return dataset
    
# 使用示例
if __name__ == "__main__":
    # 初始化生成器
    generator = TrainingDataGenerator()
    
    # 生成训练数据
    code_function_path = "../data/analyze_function.json"
    dataset = generator.generate_from_codebase(code_function_path)
    
    # 保存结果
    training_data_path = "../data/training_data.json"

    # # 生成训练样本
    # training_samples = generator.generate_complete_training_samples()
    
    with open(training_data_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Generated {len(dataset)} training  samples")
    print(f"✓ Generated {dataset['metadata']['total_qa_pairs']} Question-Answer pairs")
    print(f"✓ Training data saving in: {training_data_path}")

    # training_data = json.load(open(training_data_path, 'r')) 
    # for data in training_data:
    #     print(data)
    #     input()
    