#!/usr/bin/env python3
"""
DSL 编译器 LLM 增强功能使用示例

展示如何使用不同的LLM提供商将自然语言转换为DSL代码
"""

import os
from pathlib import Path
from dsl_compiler.config import CompilerConfig
from dsl_compiler.compiler import DSLCompiler


def example_with_dashscope():
    """使用 DashScope (阿里云) 的示例"""
    print("=== 使用 DashScope (阿里云) 示例 ===")
    
    # 配置 DashScope
    config = CompilerConfig(
        llm_enabled=True,
        llm_provider="dashscope",
        llm_model="qwen-turbo",
        llm_api_key="your_dashscope_api_key_here",  # 替换为您的API Key
        output_format="yaml"
    )
    
    # 或者通过环境变量配置
    # os.environ["DSL_LLM_PROVIDER"] = "dashscope"
    # os.environ["DSL_LLM_MODEL"] = "qwen-turbo"  
    # os.environ["DASHSCOPE_API_KEY"] = "your_api_key"
    # config = CompilerConfig.from_env()
    
    compiler = DSLCompiler(config)
    
    # 编译自然语言文件
    input_file = Path("sop_test_cases/level_1_simple_natural.txt")
    
    try:
        print(f"编译文件: {input_file}")
        dsl_output = compiler.compile(input_file)
        
        # 保存结果
        output_file = Path("output_dashscope.yaml")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(dsl_output.to_yaml())
        
        print(f"✓ 编译成功，结果保存到: {output_file}")
        print(f"生成任务数: {len(dsl_output.tasks)}")
        
    except Exception as e:
        print(f"❌ 编译失败: {e}")


def example_with_openai():
    """使用 OpenAI 的示例"""
    print("=== 使用 OpenAI 示例 ===")
    
    # 配置 OpenAI
    config = CompilerConfig(
        llm_enabled=True,
        llm_provider="openai",
        llm_model="gpt-3.5-turbo",
        llm_api_key="your_openai_api_key_here",  # 替换为您的API Key
        llm_api_base="https://api.openai.com/v1",  # 可选，自定义端点
        output_format="json"
    )
    
    # 或者通过环境变量配置
    # os.environ["DSL_LLM_PROVIDER"] = "openai"
    # os.environ["DSL_LLM_MODEL"] = "gpt-3.5-turbo"
    # os.environ["OPENAI_API_KEY"] = "your_api_key"
    # config = CompilerConfig.from_env()
    
    compiler = DSLCompiler(config)
    
    input_file = Path("sop_test_cases/level_1_simple_natural.txt")
    
    try:
        print(f"编译文件: {input_file}")
        dsl_output = compiler.compile(input_file)
        
        # 保存为JSON格式
        output_file = Path("output_openai.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(dsl_output.to_json(compact=False))
        
        print(f"✓ 编译成功，结果保存到: {output_file}")
        print(f"生成任务数: {len(dsl_output.tasks)}")
        
    except Exception as e:
        print(f"❌ 编译失败: {e}")


def example_without_llm():
    """不使用LLM增强的示例"""
    print("=== 不使用 LLM 增强示例 ===")
    
    # 禁用LLM
    config = CompilerConfig(
        llm_enabled=False,
        output_format="yaml"
    )
    
    compiler = DSLCompiler(config)
    
    # 编译已经结构化的DSL文件
    input_file = Path("example/password_reset_dsl.txt")
    
    try:
        print(f"编译文件: {input_file}")
        dsl_output = compiler.compile(input_file)
        
        output_file = Path("output_no_llm.yaml")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(dsl_output.to_yaml())
        
        print(f"✓ 编译成功，结果保存到: {output_file}")
        print(f"生成任务数: {len(dsl_output.tasks)}")
        
    except Exception as e:
        print(f"❌ 编译失败: {e}")


def example_cli_usage():
    """命令行使用示例"""
    print("=== 命令行使用示例 ===")
    
    examples = [
        "# 使用 DashScope",
        "DSL_LLM_PROVIDER=dashscope DASHSCOPE_API_KEY=your_key uv run dslc compile sop_test_cases/level_1_simple_natural.txt",
        "",
        "# 使用 OpenAI", 
        "DSL_LLM_PROVIDER=openai OPENAI_API_KEY=your_key uv run dslc compile sop_test_cases/level_1_simple_natural.txt",
        "",
        "# 禁用 LLM",
        "uv run dslc compile example/password_reset_dsl.txt --no-llm",
        "",
        "# 指定输出格式",
        "uv run dslc compile sop_test_cases/level_1_simple_natural.txt --format json",
        "",
        "# 调试模式",
        "uv run dslc compile sop_test_cases/level_1_simple_natural.txt --debug",
    ]
    
    for example in examples:
        print(example)


def main():
    """主函数"""
    print("DSL 编译器 LLM 增强功能使用示例\n")
    
    # 检查测试文件是否存在
    natural_file = Path("sop_test_cases/level_1_simple_natural.txt")
    dsl_file = Path("example/password_reset_dsl.txt")
    
    if not natural_file.exists():
        print(f"❌ 测试文件不存在: {natural_file}")
        return
    
    if not dsl_file.exists():
        print(f"❌ 测试文件不存在: {dsl_file}")
        return
    
    print("可用的示例:")
    print("1. DashScope (阿里云) 示例")
    print("2. OpenAI 示例") 
    print("3. 不使用LLM示例")
    print("4. 命令行使用示例")
    print()
    
    # 运行不需要API Key的示例
    example_without_llm()
    print()
    
    example_cli_usage()
    print()
    
    print("注意事项:")
    print("- 使用LLM功能需要配置相应的API Key")
    print("- DashScope需要阿里云账号和API Key")
    print("- OpenAI需要OpenAI账号和API Key")
    print("- 可以通过环境变量或配置文件设置参数")
    print("- LLM会将自然语言直接转换为DSL代码格式")


if __name__ == "__main__":
    main() 