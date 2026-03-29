#!/usr/bin/env python3
"""
Main pyinfra deployment script with proper timeout handling for web requests.
"""

import argparse
import sys
from typing import Optional

from pyinfra import host, local
from pyinfra.api import Config
from pyinfra.api.exceptions import PyinfraError


def parse_bool(value: str) -> bool:
    """Parse a boolean value from command line arguments."""
    if value.lower() in ("true", "t", "yes", "y", "1"):
        return True
    elif value.lower() in ("false", "f", "no", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Pyinfra deployment script")
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=30,
        help="Timeout in seconds for web requests (default: 30)"
    )
    parser.add_argument(
        "--retries", 
        type=int, 
        default=3,
        help="Number of retry attempts for failed requests (default: 3)"
    )
    parser.add_argument(
        "--retry-delay", 
        type=int, 
        default=5,
        help="Delay between retry attempts in seconds (default: 5)"
    )
    parser.add_argument(
        "--install-vault", 
        type=parse_bool, 
        default=False,
        help="Install HashiCorp Vault CLI (default: False)"
    )
    parser.add_argument(
        "--install-lazygit", 
        type=parse_bool, 
        default=False,
        help="Install lazygit (default: False)"
    )
    parser.add_argument(
        "--install-git-lfs", 
        type=parse_bool, 
        default=False,
        help="Install Git LFS (default: False)"
    )
    
    args = parser.parse_args()
    
    # Configure pyinfra with timeout settings
    config = Config(
        TIMEOUT=args.timeout,
        FAIL_PERCENT=100,
        PARALLEL=1,
    )
    
    try:
        # Import operations dynamically to avoid import errors if not available
        if args.install_vault:
            try:
                from pyinfra_collections.runtime_environments.operations.vault import install_hashicorp_vault_cli
                print("Installing HashiCorp Vault CLI...")
                result = install_hashicorp_vault_cli(timeout=args.timeout)
                if result.get("success"):
                    print(f"✓ {result.get('output')}")
                else:
                    print(f"✗ Failed to install Vault CLI: {result.get('output')}")
                    sys.exit(1)
            except ImportError as e:
                print(f"✗ Failed to import Vault CLI operations: {e}")
                sys.exit(1)
        
        if args.install_lazygit:
            try:
                from pyinfra_collections.development_tools.operations.lazygit import install_lazygit
                print("Installing lazygit...")
                result = install_lazygit(timeout=args.timeout)
                if result.get("success"):
                    print(f"✓ {result.get('output')}")
                else:
                    print(f"✗ Failed to install lazygit: {result.get('output')}")
                    sys.exit(1)
            except ImportError as e:
                print(f"✗ Failed to import lazygit operations: {e}")
                sys.exit(1)
        
        if args.install_git_lfs:
            try:
                from pyinfra_collections.development_tools.operations.git_lfs import install_git_lfs
                print("Installing Git LFS...")
                result = install_git_lfs(timeout=args.timeout)
                if result.get("success"):
                    print(f"✓ {result.get('output')}")
                else:
                    print(f"✗ Failed to install Git LFS: {result.get('output')}")
                    sys.exit(1)
            except ImportError as e:
                print(f"✗ Failed to import Git LFS operations: {e}")
                sys.exit(1)
        
        print("Deployment completed successfully!")
        
    except PyinfraError as e:
        print(f"✗ Deployment failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("✗ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()