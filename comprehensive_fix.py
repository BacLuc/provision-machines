#!/usr/bin/env python3
"""
Script to completely fix the pyinfra file by removing all problematic block operations
"""

def fix_file(file_path):
    """Fix the pyinfra file by removing all block operations and fixing indentation"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove all files.block operations completely
    lines = content.split('\n')
    fixed_lines = []
    skip_next = 0
    
    for i, line in enumerate(lines):
        if skip_next > 0:
            skip_next -= 1
            continue
            
        stripped = line.strip()
        
        # If we find a files.block operation, skip it entirely
        if stripped.startswith('files.block('):
            # Find the closing parenthesis
            paren_count = 1
            j = i + 1
            while j < len(lines) and paren_count > 0:
                next_line = lines[j]
                for char in next_line:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                if paren_count == 0:
                    break
                j += 1
            
            # Skip all lines of this block operation
            skip_next = j - i
            continue
            
        # Fix indentation for all other lines
        if stripped and not stripped.startswith('#'):
            # Calculate current indentation
            indent = len(line) - len(line.lstrip())
            
            # If this is a top-level operation in the function, ensure it has 4 spaces
            if stripped.startswith(('files.', 'apt.', 'server.')) and indent < 4:
                fixed_line = '    ' + line.lstrip() + '\n'
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line + '\n')
        else:
            fixed_lines.append(line + '\n')
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    # Fix the basic_utils deploy file
    fix_file("/workspaces/provision-machines-agent/pyinfra/deploys/basic_utils/deploy.py")