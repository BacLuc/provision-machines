#!/usr/bin/env python3
"""
Pyinfra local deployment script for provisioning machines.
This script runs the pyinfra deployment locally.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Main deployment function."""
    print("Starting pyinfra local deployment...")
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    pyinfra_dir = project_root / "pyinfra"
    
    # Change to the pyinfra directory
    os.chdir(pyinfra_dir)
    
    # Run pyinfra using the CLI
    try:
        # Run pyinfra with the local inventory and deploy.py
        result = subprocess.run(
            ["pyinfra", "-vvv", "-y", "@local", "deploy.py"],
            cwd=pyinfra_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Deployment completed successfully!")
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
        else:
            print(f"Deployment failed with return code: {result.returncode}")
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            return 1
            
    except FileNotFoundError:
        print("pyinfra command not found. Make sure pyinfra is installed.")
        return 1
    except Exception as e:
        print(f"Error during deployment: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())