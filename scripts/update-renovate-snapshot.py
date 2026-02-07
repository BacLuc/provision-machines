#!/usr/bin/env python3
"""
Sophisticated script to parse Renovate dry-run output and generate YAML snapshot.
Handles incomplete/truncated JSON by extracting what we can.
"""

import json
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

def extract_json_safely(content: str) -> Dict:
    """Extract and parse JSON from the debug output safely."""
    
    # Remove the first debug line if present
    lines = content.split('\n')
    if lines and 'packageFiles' in lines[0]:
        content = '\n'.join(lines[1:])
    
    # Clean up leading spaces
    content = '\n'.join(line.lstrip() for line in content.split('\n'))
    
    # Find the config object and make it complete
    content = content.strip()
    if content.startswith('"config":'):
        content = '{' + content
    
    # Try to fix common JSON issues
    # Remove trailing commas before closing braces
    content = re.sub(r',(\s*})', r'\1', content)
    
    # Try to parse progressively larger portions
    for i in range(len(content), 0, -100):
        if i < 100:
            i = 100
        
        test_content = content[:i]
        
        # Count braces to see if we have a complete object
        brace_count = test_content.count('{') - test_content.count('}')
        
        if brace_count <= 0:  # We have a complete or mostly complete object
            # Try to close it properly
            if brace_count < 0:
                # Not enough closing braces, add them
                test_content += '}' * (-brace_count)
            
            try:
                data = json.loads(test_content)
                print(f"Successfully parsed JSON with {len(test_content)} characters")
                return data
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON of length {len(test_content)}: {e}")
                if i <= 100:
                    # Try without the error location
                    try:
                        simplified = test_content[:e.pos-1].rstrip(',') + '}'
                        return json.loads(simplified)
                    except:
                        pass
                continue
    
    raise ValueError("Could not parse JSON from any portion of the content")

def extract_dependencies(package_files: Dict) -> List[Dict]:
    """Extract dependencies from package files structure."""
    deps = []
    
    for manager, files in package_files.items():
        if not isinstance(files, list):
            continue
            
        for file_info in files:
            if not isinstance(file_info, dict) or 'deps' not in file_info:
                continue
                
            file_path = file_info.get('packageFile', 'unknown')
            file_deps = file_info.get('deps', [])
            
            for dep_info in file_deps:
                if not isinstance(dep_info, dict):
                    continue
                
                # Skip dependencies with clearly invalid names
                dep_name = dep_info.get('depName', '')
                if not dep_name or dep_name.startswith('${'):
                    continue
                
                # Extract version information
                current_value = dep_info.get('currentValue', '')
                current_digest = dep_info.get('currentDigest', '')
                
                # Use digest if available, otherwise use version
                version = current_digest if current_digest else current_value
                
                dep = {
                    'name': dep_name,
                    'version': version,
                    'datasource': dep_info.get('datasource', ''),
                    'file_path': file_path,
                    'dep_type': dep_info.get('depType'),
                    'package_name': dep_info.get('packageName'),
                    'skip_reason': dep_info.get('skipReason')
                }
                
                # Only include dependencies with valid names and either version or skip reason
                if dep['name'] and (dep['version'] or dep['skip_reason']):
                    deps.append(dep)
    
    return deps

def generate_yaml_snapshot(dependencies: List[Dict], output_file: str) -> bool:
    """Generate a YAML snapshot file."""
    
    # Group dependencies by datasource
    grouped = defaultdict(list)
    for dep in dependencies:
        grouped[dep['datasource']].append(dep)
    
    # Build YAML structure (simple format - no versions, no total count)
    snapshot = {
        'dependency_groups': {}
    }
    
    # Add grouped dependencies with nice names
    type_names = {
        'docker': 'Docker Images',
        'github-releases': 'GitHub Releases', 
        'git-refs': 'Git References',
        'github-tags': 'GitHub Tags',
        'github-runners': 'GitHub Runners',
        'gitlabci': 'GitLab CI'
    }
    
    for datasource, deps in grouped.items():
        group_name = type_names.get(datasource, datasource.title())
        snapshot['dependency_groups'][group_name] = []
        
        for dep in sorted(deps, key=lambda d: (d['file_path'], d['name'])):
            dep_entry = {
                'file': dep['file_path'],
                'name': dep['name'],
                'datasource': dep['datasource']
            }
            
            if dep['dep_type']:
                dep_entry['type'] = dep['dep_type']
            if dep['package_name'] and dep['package_name'] != dep['name']:
                dep_entry['package_name'] = dep['package_name']
            if dep['skip_reason']:
                dep_entry['skip_reason'] = dep['skip_reason']
            
            snapshot['dependency_groups'][group_name].append(dep_entry)
    
    # Write YAML file
    try:
        with open(output_file, 'w') as f:
            # Write header comments
            f.write("# Renovate Dependency Snapshot\n")
            f.write("# This file contains all dependencies detected by Renovate\n")
            f.write("# Auto-generated by update-renovate-snapshot.py\n\n")
            
            # Write YAML content
            yaml.dump(snapshot, f, default_flow_style=False, indent=2, sort_keys=False)
        
        print(f"Generated YAML snapshot: {output_file}")
        print(f"Total dependencies: {len(dependencies)}")
        
        # Print summary by type
        for group_name in sorted(grouped.keys()):
            deps = grouped[group_name]
            nice_name = type_names.get(group_name, group_name.title())
            print(f"  {nice_name}: {len(deps)}")
        
        return True
        
    except Exception as e:
        print(f"Error writing YAML file: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 update-renovate-snapshot.py <renovate_output_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else '.github/renovate-snapshot.yaml'
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"Error: Input file {input_file} does not exist")
        sys.exit(1)
    
    try:
        # Read the content
        with open(input_file, 'r') as f:
            content = f.read()
        
        # Parse output
        data = extract_json_safely(content)
        
        if 'config' not in data:
            print("Error: Invalid structure - no 'config' key found")
            print("Available keys:", list(data.keys()))
            sys.exit(1)
        
        # Extract dependencies
        dependencies = extract_dependencies(data['config'])
        
        if not dependencies:
            print("Warning: No dependencies found in output")
            sys.exit(1)
        
        # Generate snapshot
        success = generate_yaml_snapshot(dependencies, output_file)
        
        if not success:
            sys.exit(1)
        
        print("✅ Snapshot generation completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()