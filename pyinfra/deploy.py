from operations.filesystem import dirname_of
import os
import sys

# Get the directory containing this file
current_dir = dirname_of(__file__)
deploys_dir = os.path.join(current_dir, "deploys")

# Add the deploys directory to the Python path
sys.path.insert(0, deploys_dir)

# Import and run each deploy
try:
    # Import basic_utils first
    from basic_utils.deploy import deploy as basic_utils_deploy
    print("Running basic_utils deploy...")
    basic_utils_deploy()
    
    # Import and run other deploys as needed
    # For now, let's just run basic_utils to test
    print("Basic utils deploy completed successfully!")
    
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error running deploy: {e}")
