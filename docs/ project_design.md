<!--设计文档   -->
# 本地代码仓智能训练数据生成与处理设计文档

## 一、项目概述

本项目旨在依据本地代码仓的业务流程和规则，自动化生成问答对训练数据。这些问答对不仅包含问答内容，还附带原文代码段及推理过程，以提升模型对代码相关问题的理解和回答能力。项目将使用 GitHub 公开代码仓库进行训练集生成和测试，确保数据来源的丰富性和多样性。

## 二、训练集结构设计

### 场景一： 问答对形式

每个问答对将采用以下 JSON 格式进行存储，包含问答对、推理过程和元数据，方便后续的处理和使用：

```json
json{
    "question": "这个TF_DataTypeSize函数是做什么的？",
    "answer": "TF_DataTypeSize函数接收1个参数，主要用于执行特定业务逻辑。",
    "type": "function_purpose",
    "function": "TF_DataTypeSize",
    "file": "tf_datatype.cc",
    "language": "cpp",
    "code_context": {
    "function": "TF_DataTypeSize",
    "parameter": [
        "dt"
    ]
    },
    "reasoning": {
    "reasoning_type": "function_purpose",
    "reasoning_steps": [
        "分析函数名称和命名规范，从中提取功能线索",
        "检查函数参数列表，推断输入输出关系",
        "查看函数体中的关键操作和返回值",
        "查找函数文档字符串或注释（如果有）",
        "分析函数在代码库中的调用位置和上下文",
        "综合以上信息总结函数的主要功能和目的"
    ],
    "example_answer": "通过分析函数名'TF_DataTypeSize'，结合参数类型和函数体中的主要操作，可以推断该函数主要用于执行特定业务逻辑",
    "reasoning_chain": "推理过程分析：\n\n代码上下文：\n文件：未知\n行号：未知\n\n推理步骤：\n1. 分析函数名称和命名规范，从中提取功能线索\n2. 检查函数参数列表，推断输入输出关系\n3. 查看函数体中的关键操作和返回值\n4. 查找函数文档字符串或注释（如果有）\n5. 分析函数在代码库中的调用位置和上下文\n6. 综合以上信息总结函数的主要功能和目的\n\n推理结论：通过分析函数名'TF_DataTypeSize'，结合参数类型和函数体中的主要操作，可以推断该函数主要用于执行特定业务逻辑"
    },
    "difficulty": "easy",
    "generated_at": "2025-12-08T16:22:52.468966"
}
```

### 场景二： 给定需求设计方案：
```json
json{
    "requirement": "为系统添加实时通知功能",
    "design_pattern": "CRUD操作",
    "description": "实现创建、读取、更新、删除操作的标准模式",
    "components": [
      {
        "name": "Controller",
        "responsibility": "负责controller相关逻辑",
        "implementation": "需要新开发",
        "status": "new"
      },
      {
        "name": "Service",
        "responsibility": "负责service相关逻辑",
        "implementation": "需要新开发",
        "status": "new"
      },
      {
        "name": "Repository",
        "responsibility": "负责repository相关逻辑",
        "implementation": "需要新开发",
        "status": "new"
      },
      {
        "name": "Model",
        "responsibility": "负责model相关逻辑",
        "implementation": "需要新开发",
        "status": "new"
      }
    ],
    "implementation_steps": [
      "1. 分析现有代码结构，确定CRUD操作模式的适配点",
      "2. 设计CRUD操作模式的组件接口",
      "3. 实现CRUD操作模式的核心组件",
      "4. 编写单元测试确保功能正确性",
      "5. 集成到现有系统并进行端到端测试",
      "6. 编写使用文档和API文档"
    ],
    "integration_points": [
      "与现有的数据模型集成",
      "与业务逻辑层集成",
      "与API接口层集成"
    ]
  }
```

### 确保数据多样性和代表性的方法

1. **代码仓库选择**：从 GitHub 上选择多个不同领域、不同规模的公开代码仓库，涵盖常见的编程语言（如 Python、Java、JavaScript 等）。这样可以确保数据来源的多样性，使训练数据能够覆盖各种实际应用场景。
2. **文件和函数筛选**：在每个代码仓库中，随机选择不同类型文件（如源文件、测试文件、配置文件等）中的函数作为问答对的生成源。避免只选择特定类型的文件或函数，以保证数据的代表性，筛选后缀名为：['.c', '.h', '.cpp', '.cxx', '.cc', '.hpp', '.ipp', '.java', '.py', '.pyw', '.R', '.sh', '.bash', '.zsh', '.cs', '.go', '.rs', '.scala']，以适应Java、C++、python、R ，shell等语言。
3. **问题类别和难度分布**：设计多种问题类别，如函数功能、代码逻辑、错误排查、代码优化等，并在每个类别中设置不同难度级别的问题。通过合理分配问题类别和难度级别，确保训练数据能够涵盖各种类型的代码相关问题，满足不同层次的学习需求。
4. **数据采样和去重**：在生成问答对后，对数据进行采样和去重处理。采样可以避免数据量过大，同时保证数据的随机性；去重可以避免重复的问答对进入训练集，提高数据质量。

## 三、项目目录结构

```yaml
project_name/
├── data2/      # 爬虫爬取到的原始github仓库的代码
│── data/ 
│   ├── tensorflow.json  # 爬取到的包含代码的URL地址保存的son文件
│   └── analyze_function.json  # 根据URL地址下载到的函数代码段，经过分析，保存的文件
│   └── training_data.json  # 函数分析后保存成的训练数据
│   └── design_solution.json  # 给定需求生成的设计方案保存的文件
├── code/
│   ├── repository_crawler.py  # 用于从 GitHub 爬取公开代码仓库信息的脚本
│   ├── code_analyzer.py  # 代码分析脚本，用于解析代码文件，提取函数信息
│   ├── question_generator.py  # 问答对生成脚本，根据代码分析结果生成问答对
│   ├── design_generator.py  # 设计方案生成脚本，根据给定需求生成设计方案
│   ├── utils/
│   │   ├── logging_utils.py  # 日志记录工具
│   │   └── file_utils.py  # 文件操作工具
│   └── main.py  # 项目主入口脚本，协调各个模块的运行
├── configs/
│   └── config.yaml  # 项目配置文件，包含 GitHub API 密钥、爬取仓库列表、数据处理参数等
├── docs/
│   ├── project_design.md  # 本设计文档
└── requirements.txt  # 项目依赖文件，列出项目运行所需的 Python 库及其版本
```

## 四、项目流程

1. **配置项目**：在 `configs/config.yaml` 文件中配置 GitHub API 密钥、要爬取的代码仓库列表、数据处理参数等信息。
2. **爬取代码仓库**：运行 `code/repository_crawler.py` 脚本，从 GitHub 上爬取指定的公开代码仓库信息，包括仓库 URL、文件列表等。
3. **代码分析**：运行 `code/code_analyzer.py` 脚本，对爬取到的代码仓库中的文件进行解析，提取函数信息，如函数名、参数、代码段等，分析结果保存到 'data/analyze_function.json'。
4. **生成问答对**：运行 `code/question_generator.py` 脚本，根据代码分析结果，按照设计好的问题和推理逻辑生成问答对，并保存到 `data/training_data.json` 中。
5. **生成设计方案**：运行 `code/design_generator.py` 脚本，根据给定的需求，按照设计好的推理逻辑生成设计方案，并保存到 `data/design_solution.json` 中。

## 五、GitHub 操作说明

1. **创建仓库**：在 GitHub 上创建一个新的公开仓库，用于存储项目代码和数据。
2. **克隆仓库**：在本地使用 `git clone` 命令将 GitHub 仓库克隆到本地。
3. **提交代码**：在本地完成代码编写和测试后，使用 `git add`、`git commit` 和 `git push` 命令将代码提交到 GitHub 仓库。

## 六、总结

本设计文档详细规划了本地代码仓智能训练数据生成与处理项目的训练集结构、项目目录结构、项目流程以及 GitHub 操作说明。通过合理的设计和规划，确保项目能够高效、稳定地运行，生成高质量的训练数据，为代码相关问题的模型训练提供有力支持。