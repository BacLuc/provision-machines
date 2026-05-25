#!/usr/bin/env python3
"""
Script to fix syntax errors in pyinfra files
"""

import re
import os

def fix_file(file_path):
    """Fix syntax errors in a pyinfra file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix missing commas after marker_start
    pattern = r'marker_start="# ANSIBLE MANAGED BLOCK: (.*?)"\n\s*marker_end='
    replacement = r'marker_start="# ANSIBLE MANAGED BLOCK: \1",\n        marker_end='
    content = re.sub(pattern, replacement, content)
    
    # Fix f"~ strings to just ~
    pattern = r'f"~'
    replacement = r'"~'
    content = re.sub(pattern, replacement, content)
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    # Fix the basic_utils deploy file
    fix_file("/workspaces/provision-machines-agent/pyinfra/deploys/basic_utils/deploy.py")