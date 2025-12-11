# Local Code Repository Intelligent Training Data Generation and Processing

## Overview
This project automates the generation of question-answer pairs based on the business processes and rules of local code repository. It provides both Q&A content with original code snippets/reasoning processes, and architectural design solutions for specified requirements with detailed reasoning traces.

## Features
1. **Automated Q&A Generation**  
   Generates Q&A pairs from local code repository business logic, including:
   - Original code snippets
   - Step-by-step reasoning processes
   - Contextual explanations

2. **Design Solution Generation**  
   Creates architecture design solutions for given requirements with:
   - Components
   - Implementation steps
   - Repository-specific adaptations

## Getting Started

### Prerequisites
- Python 3.x
- Virtual Environment (recommended)
- GitHub Personal Access Token

### Installation
```bash
# Clone repository
git clone https://github.com/laetella/TrainDataAI-Repo
cd TrainDataAI-Repo

# Create virtual environment
python3 -m venv traindata_env

# Activate environment
# macOS/Linux
source traindata_env/bin/activate
# Windows
traindata_env\Scripts\activate

# Install dependencies
python3 -m pip install pyyaml requests pycparser
```

## One-Step Execution
Replace the path with your own parameters
```bash
python main.py \
  --config_path "../configs/config.yaml" \
  --download_url_parent_dir "../data2/raw_data/repos" \
  --download_url_path "../data/tensorflow.json" \
  --code_path "../data2/raw_data/repos/tensorflow/" \
  --functions_path "../data/analyze_function.json" \
  --training_data_path "../data/training_data.json" \
  --design_solution_path "../data/design_solution.json"
```
## Step-by-Step Execution

### Configuration

1. **GitHub Token Setup**

Add personal GitHub token in configs/config.yaml:
```yaml
github_token: "your_personal_access_token"
```
2. **Repository Specification**
In config.yaml, specify repositories to crawl:
```yaml
crawl_repos:
  - "owner/repo_name"
  - "organization/project"
Default prefix: https://api.github.com/repos/
```

### Usage Workflow
1. **Repository Crawling**

Configure config_path in repository_crawler.py

Set download_url_parent_dir for saving URL lists (JSON format)
```bash
# Run repository crawler
python3 code/repository_crawler.py
```

2. **Code Analysis**

Configure in code_analyzer.py:

```python
raw_json_path = "path/to/crawled_data.json"
dir_path = "directory/for/downloaded_code"
functions_path = "path/to/save/function_analysis.json"
```
See docs/project_design.md for format specifications
```bash
# Run analyze code
python3 code/code_analyzer.py
```

3. **Q&A Generation**

Configure in question_generator.py:

```python
code_function_path = "path/to/function_analysis.json"
training_data_path = "path/to/save/training_data.json"
# Run Question-Answer generator
python3 code/question_generator.py
```
4. **Design Solution Generation**

Configure in design_generator.py:

```python
design_solution_file = "path/to/design_solution.json"
# Run Design generator
python3 code/design_generator.py
```

### License
MIT License - see LICENSE file for details

