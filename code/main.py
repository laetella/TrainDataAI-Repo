# main.py  # one step 
import argparse, json
from repository_crawler import get_repo_urls
from code_analyzer import get_functions, analyze_directory
from question_generator import TrainingDataGenerator
from design_generator import DesignSolutionGenerator

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str, help='the config file path (including personal github token and repositories to crawl)', default= "../configs/config.yaml") 
    parser.add_argument('--download_url_parent_dir', type=str, help='the download url path (a json file, including the urls crawled from the repos you provide in config_path) will create if not exist', default= "../data2/raw_data/repos") 
    parser.add_argument('--download_url_path', type=str, help='the download url path (a json file, including the urls crawled from the repos you provide in config_path) will create if not exist', default= "../data/tensorflow.json") 
    parser.add_argument('--code_path', type=str, help='the download code path (a directory, including the crawled code content from the repos, will create if not exist', default= "../data2/raw_data/repos/tensorflow/") 
    parser.add_argument('--functions_path', type=str, help='the analyzed code (a json file, including the code functions', default= "../data/analyze_function.json") 
    parser.add_argument('--training_data_path', type=str, help='the generated training data path (a json file, including the training data', default= "../data/training_data.json") 
    parser.add_argument('--design_solution_path', type=str, help='the generated design solution path (a json file, including the design solution', default= "../data/design_solution.json") 
    args = parser.parse_args()

    # step 1 ： get repo url
    get_repo_urls(args.config_path, args.download_url_parent_dir)

    # step 2 ： download function content from the crawled usrls
    get_functions(args.download_url_path)

    # step 3: analyze code
    code_samples = analyze_directory(args.code_path, args.functions_path)

    # step 4: generate QA pairs
    generator = TrainingDataGenerator()
    dataset = generator.generate_from_codebase(args.functions_path)
    with open(args.training_data_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Generated {len(dataset)} training  samples")
    print(f"✓ Generated {dataset['metadata']['total_qa_pairs']} Question-Answer pairs")
    print(f"✓ Training data saving in: {args.training_data_path}")

    # step 4: generate design solution
    design_generator = DesignSolutionGenerator()
    code_files = json.load(open(args.functions_path, 'r'))
    # 示例需求
    context = {
        'files': [f['file_path'] for f in code_files],
        'languages': list(set(f['language'] for f in code_files))
    }
        
    sample_requirements = [
        "为系统添加实时通知功能",
        # "实现高并发订单处理系统，支持每秒1000+订单创建，要求数据强一致",
        "需要添加用户管理功能，支持增删改查",
        "要实现文件上传和下载功能",
        "需要优化系统的查询性能"
    ]
    design_solutions = []
    for req in sample_requirements:
        solution = design_generator.generate_for_requirement(req, context)
        design_solutions.append(solution)
    
    with open(args.design_solution_path, 'w', encoding='utf-8') as f:
        json.dump(design_solutions, f, ensure_ascii=False, indent=2)
        

