#!/usr/bin/env python3
"""
Script to add pass statements to empty if blocks
"""

def fix_file(file_path):
    """Add pass statements to empty if blocks"""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    for i, line in enumerate(lines):
        fixed_lines.append(line)
        
        # Check if this line starts an if block
        stripped = line.strip()
        if stripped.startswith('if ') and stripped.endswith(':'):
            # Check if the next line is empty or a comment
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if not next_line or next_line.startswith('#'):
                    # This is an empty if block, add a pass statement
                    indent = len(line) - len(line.lstrip())
                    fixed_lines.append(' ' * (indent + 4) + 'pass\n')
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    # Fix the basic_utils deploy file
    fix_file("/workspaces/provision-machines-agent/pyinfra/deploys/basic_utils/deploy.py")