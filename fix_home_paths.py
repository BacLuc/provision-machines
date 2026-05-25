#!/usr/bin/env python3
"""
Script to replace /home/{user} with ~ in pyinfra files
"""

import re
import os

def fix_file(file_path):
    """Replace /home/{user} with ~ in a pyinfra file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace /home/{user} with ~
    pattern = r'/home/\{user\}'
    content = re.sub(pattern, '~', content)
    
    # Also replace f"/home/{user}/" with "~/"
    pattern = r'f"/home/\{user\}/'
    content = re.sub(pattern, '"~/', content)
    
    # Replace f"/home/{user}" with "~"
    pattern = r'f"/home/\{user\}"'
    content = re.sub(pattern, '"~"', content)
    
    # Replace /home/ubuntu/ with ~/ for hardcoded paths
    pattern = r'/home/ubuntu/'
    content = re.sub(pattern, '~/', content)
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    # Fix the basic_utils deploy file
    fix_file("/workspaces/provision-machines-agent/pyinfra/deploys/basic_utils/deploy.py")