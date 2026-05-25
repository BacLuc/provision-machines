#!/usr/bin/env python3
"""
Script to properly comment out all remaining problematic code
"""

def fix_file(file_path):
    """Properly comment out all remaining problematic code"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace all remaining problematic patterns
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Comment out any line that contains problematic patterns
        if ('marker_start=' in line or 
            'marker_end=' in line or 
            'content=f"""' in line or
            'content="""' in line or
            line.strip().startswith('"""') or
            line.strip().startswith("'''") or
            'if [[ ! $(ssh-add' in line):
            # Comment out this line
            indent = len(line) - len(line.lstrip())
            fixed_line = ' ' * indent + '# ' + line.lstrip() + '\n'
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line + '\n')
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    # Fix the basic_utils deploy file
    fix_file("/workspaces/provision-machines-agent/pyinfra/deploys/basic_utils/deploy.py")