#!/usr/bin/env python3
"""
Script to fix all indentation issues in pyinfra files
"""

import re
import os

def fix_file(file_path):
    """Fix all indentation issues in a pyinfra file"""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    base_indent = 0
    in_function = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
            continue
            
        # Calculate current indentation
        indent = len(line) - len(line.lstrip())
        
        # Fix function definition
        if stripped.startswith('def deploy():'):
            base_indent = indent
            in_function = True
            fixed_lines.append(line)
            continue
            
        # If we're in the function, ensure proper indentation
        if in_function:
            # All operations should be indented by 4 spaces from the function definition
            expected_indent = base_indent + 4
            
            # Fix the indentation
            if indent < base_indent:
                # This line is not indented enough
                fixed_line = ' ' * expected_indent + stripped + '\n'
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    # Fix the basic_utils deploy file
    fix_file("/workspaces/provision-machines-agent/pyinfra/deploys/basic_utils/deploy.py")