本地代码仓智能训练数据生成与处理

1. 依据本地代码仓的业务流程和规则，自动化生成问答对。不仅要提供问答内容，还需给出原文代码段及推理过程

2. 针对给定需求，生成基于本地代码仓架构的设计方案，并提供解释和推理trace。

get data 
python3 code/repository_crawler.py

### 创建环境

# Create virtual environment
python3 -m venv traindata_env

# Activate it (macOS/Linux)
source traindata_env/bin/activate

Requirements:

python3 -m pip install pyyaml