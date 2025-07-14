#!/usr/bin/env python3
"""
Test script to verify the project setup is working correctly.
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"🧪 Testing: {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {str(e)}")
        return False

def main():
    """Main test function."""
    print("=" * 60)
    print("Human-Text DSL Compiler - Setup Verification")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ ERROR: pyproject.toml not found. Are you in the project root?")
        return False
    
    # Check if dsl_compiler package exists
    if not Path("dsl_compiler").exists():
        print("❌ ERROR: dsl_compiler package not found")
        return False
    
    tests = [
        ("python3 --version", "Python version"),
        ("which uv", "uv installation"),
        ("uv --version", "uv version"),
        ("grep -q '\\[tool\\.uv\\]' pyproject.toml", "uv configuration in pyproject.toml"),
        ("uv sync --dry-run", "uv sync dry run"),
        ("curl -I https://pypi.tuna.tsinghua.edu.cn/simple/ | head -1", "Mirror connectivity (Tsinghua)"),
        ("uv run python -c 'import dsl_compiler; print(\"DSL Compiler import successful\")'", "DSL Compiler import"),
        ("uv run python -c 'from dsl_compiler import compile, CompilerConfig; print(\"API import successful\")'", "API import"),
        ("uv run dslc --help", "CLI help"),
    ]
    
    passed = 0
    failed = 0
    
    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
        else:
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed! The project setup is working correctly.")
        print("\nNext steps:")
        print("1. Run 'uv sync' to install dependencies")
        print("2. Run 'uv run pre-commit install' to set up git hooks")
        print("3. Try: 'uv run dslc example/test_input.txt -o output.yaml'")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed. Please check the setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 