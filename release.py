#!/usr/bin/env python3
"""
發布新版本的腳本
使用方式: python release.py [版本類型]
版本類型: patch (修復), minor (新功能), major (重大變更)
"""
import subprocess
import sys
import re
from pathlib import Path

def get_current_version():
    """從 pyproject.toml 讀取當前版本"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding="utf-8")
    
    version_match = re.search(r'version = "([^"]+)"', content)
    if not version_match:
        raise ValueError("無法找到版本號")
    
    return version_match.group(1)

def bump_version(current_version, bump_type):
    """根據類型增加版本號"""
    major, minor, patch = map(int, current_version.split('.'))
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError("無效的版本類型，請使用: patch, minor, major")
    
    return f"{major}.{minor}.{patch}"

def update_version_in_file(new_version):
    """更新 pyproject.toml 中的版本號"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding="utf-8")
    
    new_content = re.sub(
        r'version = "[^"]+"',
        f'version = "{new_version}"',
        content
    )
    
    pyproject_path.write_text(new_content, encoding="utf-8")

def run_command(cmd):
    """執行命令"""
    print(f"執行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"錯誤: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    if len(sys.argv) != 2:
        print("使用方式: python release.py [patch|minor|major]")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    if bump_type not in ["patch", "minor", "major"]:
        print("版本類型必須是: patch, minor, major")
        sys.exit(1)
    
    # 檢查工作目錄是否乾淨
    status = run_command("git status --porcelain")
    if status:
        print("錯誤: 工作目錄不乾淨，請先提交或暫存變更")
        sys.exit(1)
    
    # 獲取當前版本並計算新版本
    current_version = get_current_version()
    new_version = bump_version(current_version, bump_type)
    
    print(f"當前版本: {current_version}")
    print(f"新版本: {new_version}")
    
    # 確認發布
    confirm = input("確定要發布這個版本嗎? (y/N): ")
    if confirm.lower() != 'y':
        print("取消發布")
        sys.exit(0)
    
    # 更新版本號
    update_version_in_file(new_version)
    print(f"✅ 已更新版本號到 {new_version}")
    
    # 提交變更
    run_command("git add pyproject.toml")
    run_command(f'git commit -m "Bump version to {new_version}"')
    print("✅ 已提交版本更新")
    
    # 創建並推送 tag
    tag_name = f"v{new_version}"
    run_command(f'git tag -a {tag_name} -m "Release {tag_name}"')
    print(f"✅ 已創建 tag: {tag_name}")
    
    # 推送到遠端
    run_command("git push")
    run_command(f"git push origin {tag_name}")
    print(f"✅ 已推送到 GitHub，GitHub Actions 將自動發布到 PyPI")
    
    print(f"\n🚀 版本 {new_version} 發布完成！")
    print("您可以在以下位置查看進度:")
    print("- GitHub Actions: https://github.com/ypochien/vnpy_sinopac/actions")
    print("- PyPI: https://pypi.org/project/vnpy-sinopac/")

if __name__ == "__main__":
    main()
