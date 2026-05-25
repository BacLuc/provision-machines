#!/usr/bin/env python3
"""
Script to fix all syntax and indentation errors in pyinfra files
"""

import re
import os

def fix_file(file_path):
    """Fix all syntax and indentation errors in a pyinfra file"""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    indent_level = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            fixed_lines.append(line)
            continue
            
        # Remove extra closing parentheses
        if stripped == ')':
            # Check if the previous line was also a closing parenthesis
            if fixed_lines and fixed_lines[-1].strip() == ')':
                continue  # Skip this extra closing parenthesis
        
        # Fix marker_end indentation
        if stripped.startswith('marker_end='):
            # Ensure marker_end has proper indentation (same as marker_start)
            fixed_line = '        ' + line.lstrip()
            fixed_lines.append(fixed_line)
            continue
            
        # Fix other indentation issues
        if stripped.startswith('content='):
            # Content should be indented more than the parameters
            fixed_line = '            ' + line.lstrip()
            fixed_lines.append(fixed_line)
            continue
            
        # Default: keep the line as is
        fixed_lines.append(line)
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    # Fix the basic_utils deploy file
    fix_file("/workspaces/provision-machines-agent/pyinfra/deploys/basic_utils/deploy.py")