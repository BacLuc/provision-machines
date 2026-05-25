from pyinfra import host
from pyinfra.operations import (
    apt,
    files,
    server,
)

# Get user from host data or use current user
import os
current_user = os.environ.get('USER', 'ubuntu')
user = host.data.get("user", current_user)

def deploy():
    # Setup user bin dir
    files.directory(
        name="Setup user bin dir",
        path="~/bin",
        mode="755",
    )
    
    print("Basic utils deploy completed successfully!")