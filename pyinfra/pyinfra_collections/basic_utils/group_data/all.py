# Default configuration for basic_utils
# These values can be overridden via --data or group_data

user = "vscode"

# Feature flags
enable_direnv = False
enable_keepassxc = False
enable_signal = False
enable_ssh_config_dir = False
ssh_agent = False
gcr_ssh_agent = False
enable_java = False
enable_flutter = False
remove_ghostty = True
enable_openvpn = False
enable_rambox = False
enable_zoom = False
enable_go = False
enable_bat = False
enable_zsh = False

# SSH key configuration
ssh_key_filename = "id_ed25519"
ssh_key_comment = "ssh-key"
gcr_ssh_agent_socket = "/run/user/1000/gcr/ssh"

# SSH config paths to include
ssh_config_paths_to_include = ["./config.d/*"]

# Python configuration
enable_python = False
python_venvs = []

# SDKMAN tools to install
sdkman_tools = []
