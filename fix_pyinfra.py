#!/usr/bin/env python3
"""
Script to remove user and group parameters from pyinfra operations
"""

import re
import os

def fix_file(file_path):
    """Remove user and group parameters from a pyinfra file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove user=user, group=user, parameters
    # This regex matches user=user, group=user, with optional whitespace
    pattern = r'user=user,\s*group=user,\s*'
    content = re.sub(pattern, '', content)
    
    # Also handle cases where user and group are on separate lines
    pattern = r'user=user,\n\s*group=user,\n'
    content = re.sub(pattern, '\n', content)
    
    # Handle individual user=user or group=user parameters
    pattern = r'user=user,\s*'
    content = re.sub(pattern, '', content)
    
    pattern = r'group=user,\s*'
    content = re.sub(pattern, '', content)
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    # Fix the basic_utils deploy file
    fix_file("/workspaces/provision-machines-agent/pyinfra/deploys/basic_utils/deploy.py")