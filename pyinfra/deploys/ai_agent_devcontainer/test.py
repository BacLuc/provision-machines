import os
import sys
import subprocess

def test_ai_agent_devcontainer():
    """Test AI Agent DevContainer setup scripts and templates"""
    
    # We can't fully test the pyinfra deployment without running pyinfra,
    # but we can check that the files are valid and in the right place.
    
    deploy_dir = os.path.dirname(os.path.abspath(__file__))
    files_dir = os.path.join(deploy_dir, "files")
    
    # Check that required files exist
    required_files = [
        "start-ai-agent-devcontainer.sh",
        "devcontainer.json",
        "compose.yml",
        "Dockerfile",
        "opencode/opencode.json"
    ]
    
    for file_path in required_files:
        full_path = os.path.join(files_dir, file_path)
        assert os.path.exists(full_path), f"Required file {file_path} is missing"
        
    # Check that the start script is valid bash
    start_script = os.path.join(files_dir, "start-ai-agent-devcontainer.sh")
    result = subprocess.run(["bash", "-n", start_script], capture_output=True, text=True)
    assert result.returncode == 0, f"Bash syntax error in start script: {result.stderr}"

if __name__ == "__main__":
    test_ai_agent_devcontainer()
    print("Tests passed!")