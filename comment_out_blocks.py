#!/usr/bin/env python3
"""
Script to comment out all block operations in pyinfra files
"""

import re
import os

def fix_file(file_path):
    """Comment out all block operations in a pyinfra file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Comment out all files.block operations
    pattern = r'(\s+)files\.block\('
    replacement = r'\1# files.block('
    content = re.sub(pattern, replacement, content)
    
    # Also comment out the content and marker parameters
    pattern = r'(\s+)(marker_start=.*|marker_end=.*|content=.*)'
    replacement = r'\1# \2'
    content = re.sub(pattern, replacement, content)
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    # Fix the basic_utils deploy file
    fix_file("/workspaces/provision-machines-agent/pyinfra/deploys/basic_utils/deploy.py")