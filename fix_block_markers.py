#!/usr/bin/env python3
"""
Script to fix block markers in pyinfra files
"""

import re
import os

def fix_file(file_path):
    """Fix block markers in a pyinfra file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace marker= with marker_start= and marker_end=
    pattern = r'marker="# ANSIBLE MANAGED BLOCK: (.*?)"'
    replacement = r'marker_start="# ANSIBLE MANAGED BLOCK: \1"\n        marker_end="# ANSIBLE MANAGED BLOCK: \1"'
    content = re.sub(pattern, replacement, content)
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    # Fix the basic_utils deploy file
    fix_file("/workspaces/provision-machines-agent/pyinfra/deploys/basic_utils/deploy.py")