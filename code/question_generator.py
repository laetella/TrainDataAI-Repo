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

class ReasoningTraceGenerator:
    """推理过程生成器"""
    
    def __init__(self):
        self.reasoning_templates = {
            'function_purpose': {
                "这个{function_name}函数是做什么的？": {
                    "steps": [
                        "分析函数名称和命名规范，从中提取功能线索",
                        "检查函数参数列表，推断输入输出关系",
                        "查看函数体中的关键操作和返回值",
                        "查找函数文档字符串或注释（如果有）",
                        "分析函数在代码库中的调用位置和上下文",
                        "综合以上信息总结函数的主要功能和目的"
                    ],
                    "example_answer": "通过分析函数名'{function_name}'，结合参数类型和函数体中的主要操作，可以推断该函数主要用于...",
                    "reasoning_trace": "步骤1：函数名称包含'{keyword}'，通常表示{explain}\n步骤2：参数包括{params}，表明需要处理{data_types}\n步骤3：函数体内有{operation}操作，返回{return_value}\n步骤4：总结功能为{purpose}"
                }
            },
            'parameter_usage': {
                "{function_name}函数的{param}参数有什么作用？": {
                    "steps": [
                        "检查参数{param}在函数签名中的位置和类型注解",
                        "查看函数体内对参数{param}的所有使用位置",
                        "分析参数{param}如何影响函数的逻辑流程",
                        "检查是否有对参数{param}的验证或转换逻辑",
                        "查看其他调用该函数时传递的参数{param}的示例",
                        "总结参数{param}的作用、约束和使用建议"
                    ],
                    "reasoning_trace": "1. 参数类型：{param_type}\n2. 在函数中的使用：{usage_context}\n3. 验证逻辑：{validation_logic}\n4. 影响结果：{impact_on_result}\n5. 使用建议：{usage_suggestion}"
                }
            },
            'code_logic': {
                "这段代码中的 {keyword} 有什么作用？": {
                    "steps": [
                        "定位代码中{keyword}的出现位置",
                        "分析{keyword}的语法角色（变量、函数、关键字等）",
                        "查看{keyword}的定义和初始化过程",
                        "跟踪{keyword}在代码流程中的变化和使用",
                        "分析{keyword}对整个算法或逻辑的贡献",
                        "评估如果没有{keyword}，代码行为会有何不同"
                    ],
                    "reasoning_trace": "定位：在第{line}行发现{keyword}\n角色：{syntactic_role}\n定义：{definition_info}\n使用：在{usage_context}中使用\n影响：对{affected_aspect}有重要影响\n替代：可以用{alternative}替代但会{consequence}"
                }
            },
            'error_handling': {
                "如果输入为空值会发生什么？": {
                    "steps": [
                        "检查代码中是否包含对空值的显式检查",
                        "分析如果没有空值检查，代码执行路径会如何变化",
                        "查看相关的异常处理机制",
                        "评估空值输入对后续处理的影响",
                        "检查是否有默认值或回退逻辑",
                        "总结空值处理的完整流程和潜在风险"
                    ],
                    "reasoning_trace": "检查点：{check_points}\n异常处理：{exception_handling}\n默认行为：{default_behavior}\n影响范围：{impact_scope}\n改进建议：{improvement_suggestion}"
                }
            },
            'optimization': {
                "这段代码在性能上有哪些优化空间？": {
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
                }
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


class EnhancedTrainingDataGenerator:
    """增强的训练数据生成器（包含推理过程）"""
    def _create_sample_contexts(self) -> Dict:
        """创建示例上下文"""
        return {
            "function_purpose": {
                "function_name": "calculate_user_score",
                "params": ["user_id", "activity_data", "weight_factors"],
                "keyword": "score",
                "operation": "加权计算和累加",
                "return_value": "整数分数",
                "purpose": "根据用户活动数据计算综合评分"
            },
            "parameter_usage": {
                "param": "weight_factors",
                "param_type": "字典类型",
                "usage_context": "各项活动的权重配置",
                "validation_logic": "检查权重和为1.0",
                "impact_on_result": "直接影响最终分数计算",
                "usage_suggestion": "传递格式为{'login': 0.3, 'post': 0.7}的字典"
            },
            "code_logic": {
                "keyword": "for循环",
                "line": 25,
                "syntactic_role": "迭代处理",
                "definition_info": "遍历用户活动列表",
                "usage_context": "累加各项活动分数",
                "affected_aspect": "处理效率和内存使用"
            },
            "error_handling": {
                "check_points": "输入验证和异常捕获",
                "exception_handling": "记录错误日志并返回默认值",
                "default_behavior": "返回0分",
                "impact_scope": "仅影响当前用户计算",
                "improvement_suggestion": "增加更详细的输入验证"
            },
            "optimization": {
                "time_complexity": "O(n)",
                "memory_usage": "O(1)",
                "bottleneck": "数据库查询次数过多",
                "optimization_suggestions": "批量查询和结果缓存",
                "expected_improvement": "性能提升30%"
            }
        }
    
    def generate_complete_training_samples(self) -> List[Dict]:
        """生成完整的训练样本（包含推理过程）"""
        
        questions = [
            # function_purpose 问题
            {
                "question": "这个calculate_user_score函数是做什么的？",
                "type": "function_purpose",
                "context": self.sample_contexts["function_purpose"]
            },
            {
                "question": "请解释calculate_user_score函数的功能",
                "type": "function_purpose", 
                "context": self.sample_contexts["function_purpose"]
            },
            
            # parameter_usage 问题
            {
                "question": "calculate_user_score函数的weight_factors参数有什么作用？",
                "type": "parameter_usage",
                "context": self.sample_contexts["parameter_usage"]
            },
            {
                "question": "参数 weight_factors 的取值范围是什么？",
                "type": "parameter_usage",
                "context": self.sample_contexts["parameter_usage"]
            },
            
            # code_logic 问题
            {
                "question": "这段代码中的 for循环 有什么作用？",
                "type": "code_logic", 
                "context": self.sample_contexts["code_logic"]
            },
            {
                "question": "循环结构在这里的作用是什么？",
                "type": "code_logic",
                "context": self.sample_contexts["code_logic"]
            },
            
            # error_handling 问题
            {
                "question": "如果输入为空值会发生什么？",
                "type": "error_handling",
                "context": self.sample_contexts["error_handling"]
            },
            {
                "question": "当输入非法参数时会有哪些表现？",
                "type": "error_handling",
                "context": self.sample_contexts["error_handling"]
            },
            
            # optimization 问题
            {
                "question": "这段代码在性能上有哪些优化空间？",
                "type": "optimization", 
                "context": self.sample_contexts["optimization"]
            },
            {
                "question": "如何减少这段代码的内存占用？",
                "type": "optimization",
                "context": self.sample_contexts["optimization"]
            }
        ]
        
        training_samples = []
        
        for q in questions:
            # 生成推理过程
            reasoning_data = self.reasoning_generator.generate_reasoning_trace(
                q["type"],
                q["question"],
                q["context"]
            )
            
            # 生成对应的答案
            answer = self._generate_answer(q["question"], q["type"], q["context"])
            
            # 构建完整训练样本
            sample = {
                "instruction": "请根据代码逻辑分析问题，提供详细的推理过程和答案",
                "input": q["question"],
                "output": answer,
                "metadata": {
                    "question_type": q["type"],
                    "context": q["context"]
                },
                "reasoning": reasoning_data
            }
            
            training_samples.append(sample)
        
        return training_samples
    
    def _generate_answer(self, question: str, question_type: str, context: Dict) -> str:
        """生成答案"""
        
        answers = {
            "function_purpose": {
                "这个calculate_user_score函数是做什么的？": 
                    "calculate_user_score函数主要用于根据用户的活动数据计算综合评分。它接收用户ID、活动数据和权重因子作为输入，通过对各项活动进行加权计算，最终返回一个整数形式的用户评分。该函数常用于用户活跃度评估和个性化推荐场景。",
                
                "请解释calculate_user_score函数的功能":
                    "calculate_user_score函数的功能可以分解为以下几个部分：\n1. 输入验证：检查用户ID有效性、活动数据格式和权重因子配置\n2. 分数计算：按照权重因子对各项活动数据进行加权计算\n3. 结果处理：将计算结果归一化到指定范围\n4. 返回结果：输出最终的评分结果\n\n该函数的设计考虑了可扩展性，便于添加新的活动类型或调整计算策略。"
            },
            "parameter_usage": {
                "calculate_user_score函数的weight_factors参数有什么作用？":
                    "weight_factors参数是一个字典类型的参数，用于指定各项活动在总分计算中的权重比例。它的主要作用包括：\n\n1. 权重配置：定义如{'login': 0.3, 'post': 0.5, 'comment': 0.2}的权重分配\n2. 计算指导：指导分数计算算法如何加权各项活动\n3. 灵活性：允许根据不同场景调整评分策略\n\n需要注意的是，权重因子的总和应为1.0，否则需要进行归一化处理。",
                
                "参数 weight_factors 的取值范围是什么？":
                    "weight_factors参数的取值范围要求如下：\n\n1. 键范围：必须是系统中定义的活动类型，如'login'、'post'、'comment'等\n2. 值范围：每个权重值应该是0到1之间的浮点数\n3. 总和要求：所有权重值的总和理论上应为1.0\n4. 特殊处理：如果总和不为1.0，系统会自动进行归一化处理\n\n示例有效值：{'login': 0.3, 'post': 0.4, 'comment': 0.3}"
            },
            "code_logic": {
                "这段代码中的 for循环 有什么作用？":
                    "代码中的for循环主要作用如下：\n\n1. 迭代处理：遍历用户的所有活动记录列表\n2. 分数累加：对每条活动记录，根据其类型和权重计算分数并累加\n3. 数据聚合：将分散的活动数据聚合成一个总分\n4. 条件检查：在循环中可以检查每项活动的有效性\n\n循环的优化建议：对于大量数据，可以考虑分批处理或使用向量化计算。",
                
                "循环结构在这里的作用是什么？":
                    "这里的循环结构承担多个重要角色：\n\n1. 遍历功能：顺序处理用户活动列表中的每个元素\n2. 计算核心：执行分数计算的主要逻辑单元\n3. 状态维护：在迭代过程中维护累加器和状态变量\n4. 异常隔离：单次循环失败不会影响其他记录的处理\n\n循环的设计考虑了性能和可读性的平衡，是算法的关键组成部分。"
            },
            "error_handling": {
                "如果输入为空值会发生什么？":
                    "当输入为空值时，代码会按照以下流程处理：\n\n1. 检查阶段：在函数入口处验证输入参数\n2. 处理逻辑：如果user_id为空，记录警告日志并返回默认分数0\n3. 容错机制：如果activity_data为空列表，视为用户无活动，返回基础分\n4. 权重缺失：如果weight_factors为空，使用默认权重配置\n\n这样的设计确保了系统的健壮性，避免因空值导致程序崩溃。",
                
                "当输入非法参数时会有哪些表现？":
                    "对于非法参数输入，系统会有以下表现：\n\n1. 类型错误：如果参数类型不正确，会抛出TypeError异常\n2. 值域异常：如果参数值超出允许范围，会返回错误码和提示信息\n3. 格式问题：如果JSON格式不正确，会尝试修复或返回解析失败\n4. 记录日志：所有非法参数都会记录到系统日志中，便于调试\n\n系统采用防御性编程，尽量从错误中恢复并提供有意义的反馈。"
            },
            "optimization": {
                "这段代码在性能上有哪些优化空间？":
                    "代码的性能优化空间主要包括：\n\n1. 算法优化：当前O(n)时间复杂度可以接受，但可以考虑并行计算\n2. 内存使用：减少中间变量的创建，使用生成器替代列表\n3. I/O优化：合并数据库查询，减少查询次数\n4. 缓存策略：对频繁计算的用户分数进行缓存\n5. 批处理：支持批量用户计算，减少函数调用开销\n\n通过这些优化，预期可以将性能提升30%以上。",
                
                "如何减少这段代码的内存占用？":
                    "减少内存占用的方法包括：\n\n1. 使用迭代器：用itertools替代列表操作\n2. 流式处理：逐个处理记录而不是一次性加载所有数据\n3. 数据压缩：对中间结果使用更紧凑的数据结构\n4. 内存复用：重用对象而不是频繁创建新对象\n5. 延迟计算：只在需要时才计算相关数据\n\n特别要注意避免在循环中创建大量临时对象。"
            }
        }
        
        # 返回具体答案，如果没有匹配则返回通用答案
        if question_type in answers and question in answers[question_type]:
            return answers[question_type][question]
        else:
            return f"根据代码分析，{question} 的答案是：该部分代码实现了特定业务逻辑，需要根据具体上下文进行分析和处理。"


def save_training_data(dataset, filename: str ):
    """保存训练数据"""
    
    # dataset = {
    #     "description": "代码理解和推理问答训练数据（包含推理过程）",
    #     "version": "1.0",
    #     "created_at": "2025-01-15",
    #     "samples_count": len(samples),
    #     "samples": samples
    # }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 已生成 {len(dataset)} 个训练样本")
    print(f"✓ 已生成 {dataset['metadata']['total_qa_pairs']} 个问答对")
    print(f"✓ 训练数据已保存到: {filename}")

class QAPairGenerator:
    """问答对生成器"""
    
    def __init__(self):
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
        
        # 1. 函数目的问答
        for template in self.qa_templates['function_purpose']:
            question = template.format(function_name=func_name)
            answer = self._generate_function_purpose_answer(func)
            qa_pairs.append({
                'question': question,
                'answer': answer,
                'type': 'function_purpose',
                'context': {'function': func_name},
                'difficulty': 'easy'
            })
        
        # 2. 参数相关问答
        for param in func.get('params', [])[:3]:  # 只取前3个参数
            for template in self.qa_templates['parameter_usage']:
                question = template.format(function_name=func_name, param=param)
                answer = f"参数'{param}'用于{self._guess_param_purpose(param, func)}"
                qa_pairs.append({
                    'question': question,
                    'answer': answer,
                    'type': 'parameter_usage',
                    'context': {'function': func_name, 'parameter': param},
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
                'difficulty': 'medium'
            })
        # 代码逻辑问题
        if 'loop' in func.get('body', ''):
            qa_pairs.append({
                'question': self.qa_templates['code_logic'][1],
                'answer': "循环结构用于处理重复逻辑或遍历数据集合",
                'category': 'code_logic',
                'context': {'function': func_name},
                'difficulty': 'medium'
            })
        
        # 错误处理问题
        qa_pairs.append({
            'question': random.choice(self.qa_templates['error_handling']),
            'answer': "需要添加输入验证和异常处理机制",
            'category': 'error_handling',
            'context': {'function': func_name},
            'difficulty': 'hard'
        })
        
        # 优化建议问题
        if func.get('body', '').count('\n') > 10:
            qa_pairs.append({
                'question': random.choice(self.qa_templates['optimization']),
                'answer': "可以考虑使用更高效的数据结构或算法",
                'category': 'optimization',
                'context': {'function': func_name},
                'difficulty': 'hard'
            })
        
        return qa_pairs
    
    def _generate_function_purpose_answer(self, func: Dict) -> str:
        """生成函数目的答案"""
        func_name = func.get('name', '')
        params = func.get('params', [])
        
        # 根据函数名猜测功能
        purpose_guess = self._guess_function_purpose(func_name)
        
        if func.get('docstring'):
            return f"{func_name}函数用于{purpose_guess}。文档说明：{func.get('docstring')[:100]}..."
        else:
            return f"{func_name}函数接收{len(params)}个参数，用于{purpose_guess}"
    
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
        self.reasoning_generator = ReasoningTraceGenerator()
        
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
            
            # # 从文件结构生成问答
            # qa_pairs.extend(self.qa_generator.generate_from_file_structure(code_file))
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
    
    # 保存训练数据
    save_training_data(dataset, training_data_path)
    