#!/usr/bin/env python3

import os
import sys
from argparse import ArgumentParser
from cli_interface import run_cli_mode
from gui_interface import run_gui_mode

def main():
    # Parse command-line arguments
    parser = ArgumentParser(description="Secure Disk Eraser Tool")
    parser.add_argument('--cli', action='store_true', help="Run in command-line mode instead of GUI")
    parser.add_argument('-f', '--filesystem', choices=['ext4', 'ntfs', 'vfat'], help="Filesystem type to use")
    parser.add_argument('-p', '--passes', type=int, default=5, help="Number of passes for erasure")
    parser.add_argument('--crypto', action='store_true', help="Use cryptographic erasure instead of standard multi-pass method")
    args = parser.parse_args()
    
    # Check for root privileges
    if os.geteuid() != 0:
        print("This program must be run as root!")
        sys.exit(1)
    
    # Choose mode based on arguments
    if args.cli:
        # Run the original CLI version
        run_cli_mode(args)
    else:
        # Run the GUI version
        run_gui_mode()

if __name__ == "__main__":
    main()