import sys
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from subprocess import CalledProcessError, SubprocessError

from disk_erase import get_disk_serial, is_ssd
from disk_operations import get_active_disk, process_disk  # Import process_disk from disk_operations
from utils import list_disks, choose_filesystem
from log_handler import log_info, log_error

def print_disk_details(disk):
    """Print detailed information about a disk."""
    try:
        disk_id = get_disk_serial(disk)
        is_disk_ssd = is_ssd(disk)
        active_disks = get_active_disk()        
        
        # Fix: Check if any active disk name is a substring of this disk name
        is_active = False
        if active_disks:
            for active_disk in active_disks:
                if active_disk in disk:
                    is_active = True
                    break
        
        print(f"Disk: /dev/{disk}")
        print(f"  Serial/ID: {disk_id}")
        print(f"  Type: {'SSD' if is_disk_ssd else 'HDD'}")
        print(f"  Status: {'ACTIVE SYSTEM DISK - DANGER!' if is_active else 'Safe to erase'}")
        
        if is_disk_ssd:
            print("  WARNING: This is an SSD device. Multiple-pass secure erasure:")
            print("    • May damage the SSD by causing excessive wear")
            print("    • May not securely erase all data due to SSD wear leveling")
            print("    • May not overwrite all sectors due to over-provisioning")
            print("    • Manufacturer-provided secure erase tools are recommended")
        
        if is_active:
            print("  DANGER: This is the ACTIVE SYSTEM DISK! Erasing it will make your system unusable.")
            print("          The system will crash if you proceed with erasing this disk.")
            
        return disk_id, is_disk_ssd, is_active
    except (SubprocessError, FileNotFoundError) as e:
        print(f"Error getting disk details: {str(e)}")
        log_error(f"Error getting disk details for {disk}: {str(e)}")
        return f"unknown_{disk}", False, False

def select_disks() -> list[str]:
    """
    Let the user select disks to erase from the command line, with detailed information.
    """
    try:
        disk_list = list_disks()
        if not disk_list:
            print("No disks detected.")
            return []
        
        print("\n=== Available Disks ===")
        print(disk_list)
        print("\n=== Detailed Disk Information ===")
        
        available_disks = []
        for line in disk_list.strip().split('\n'):
            if not line.strip():
                continue
                
            parts = line.strip().split(maxsplit=3)
            if len(parts) >= 1:
                available_disks.append(parts[0])
        
        # Print detailed information for each disk
        for disk in available_disks:
            print("\n" + "-" * 50)
            print_disk_details(disk)
        
        print("\n" + "-" * 50)
        print("\nWARNING: This tool will COMPLETELY ERASE selected disks. ALL DATA WILL BE LOST!")
        print("WARNING: If any of these disks are SSDs, using this tool with multiple passes may damage the SSD.")
        print("For SSDs, manufacturer-provided secure erase tools are recommended.\n")
        
        selected_disks = input("Enter the disks to erase (comma-separated, e.g., sda,sdb): ").strip()
        disk_names = [disk.strip() for disk in selected_disks.split(",") if disk.strip()]
        
        valid_disks = []
        for disk in disk_names:
            if re.match(r'^[a-zA-Z]+[0-9]*$', disk):
                disk_path = f"/dev/{disk}"
                if os.path.exists(disk_path):
                    valid_disks.append(disk)
                else:
                    print(f"Disk {disk_path} not found. Skipping.")
            else:
                print(f"Invalid disk name format: {disk}. Skipping.")
        
        return valid_disks
        
    except KeyboardInterrupt:
        log_error("Disk selection interrupted by user (Ctrl+C)")
        sys.exit(130)
    except IOError as e:
        log_error(f"I/O error: {str(e)}")
        return []

def confirm_erasure(disk: str) -> bool:
    """
    Get confirmation to erase a specific disk with detailed warnings.
    """
    while True:
        try:
            print("\n" + "-" * 50)
            disk_id, is_disk_ssd, is_active = print_disk_details(disk)
            print("-" * 50)
            
            if is_disk_ssd:
                print("\nWARNING: This disk is an SSD. Secure erasure may not be guaranteed.")
                print("         Multiple passes may damage the SSD.")
                
            if is_active:
                print("\nDANGER: This is the ACTIVE SYSTEM DISK! Erasing it will make your system unusable.")
                print("        The system will CRASH if you proceed with erasing this disk.")
                
            print(f"\nYou are about to PERMANENTLY ERASE disk {disk_id} (/dev/{disk}).")
            print("This operation CANNOT be undone and ALL DATA WILL BE LOST!")
            
            confirmation = input(f"Are you sure you want to erase disk {disk_id}? (yes/no): ").strip().lower()
            if confirmation == "yes":
                # For active system disks, require a second confirmation
                if is_active:
                    second_confirm = input("FINAL WARNING: You are about to erase the ACTIVE SYSTEM DISK. Type 'DESTROY' to confirm: ").strip()
                    return second_confirm == "DESTROY"
                return True
            elif confirmation == "no":
                return False
            print("Invalid input. Enter 'yes' or 'no'.")
        except KeyboardInterrupt:
            log_error("Erasure confirmation interrupted by user (Ctrl+C)")
            sys.exit(130)

def get_disk_confirmations(disks: list[str]) -> list[str]:
    """Get confirmation for each disk."""
    return [disk for disk in disks if confirm_erasure(disk)]

def cli_process_disk(disk, fs_choice, passes, use_crypto=False):
    """
    Process a single disk for the CLI interface with status output.
    
    This function wraps the process_disk function from disk_operations.py
    to provide CLI-specific logging and error handling.
    """
    try:
        # Get the disk identifier for better logging
        disk_id = get_disk_serial(disk)
        print(f"\nProcessing disk {disk_id} (/dev/{disk})...")
        
        # Define a logging function for the CLI
        def log_progress(message):
            print(f"  {message}")
        
        # Indicate if the disk is an SSD and not using crypto
        if is_ssd(disk) and not use_crypto:
            print(f"  WARNING: {disk_id} is an SSD - multiple-pass erasure may not be effective")
        
        # Process the disk using the imported function with crypto flag
        process_disk(disk, fs_choice, passes, use_crypto, log_func=log_progress)
        
        print(f"Successfully completed all operations on disk {disk_id}")
        return True
    except (CalledProcessError, SubprocessError) as e:
        print(f"Error processing disk /dev/{disk}: {str(e)}")
        log_error(f"Error processing disk /dev/{disk}: {str(e)}")
        return False
    except IOError as e:
        print(f"I/O error while processing disk /dev/{disk}: {str(e)}")
        log_error(f"I/O error while processing disk /dev/{disk}: {str(e)}")
        return False
    except OSError as e:
        print(f"OS error while processing disk /dev/{disk}: {str(e)}")
        log_error(f"OS error while processing disk /dev/{disk}: {str(e)}")
        return False
    except ValueError as e:
        print(f"Value error while processing disk /dev/{disk}: {str(e)}")
        log_error(f"Value error while processing disk /dev/{disk}: {str(e)}")
        return False
    except KeyboardInterrupt:
        print(f"Disk processing interrupted for /dev/{disk}")
        log_error(f"Disk processing interrupted for /dev/{disk}")
        return False

def run_cli_mode(args):
    """
    Run the command-line interface version with detailed disk information.
    """
    try:
        # Check for root privileges
        if os.geteuid() != 0:
            print("Error: This program must be run as root!")
            sys.exit(1)
            
        print("=" * 60)
        print("         SECURE DISK ERASER - COMMAND LINE INTERFACE")
        print("=" * 60)
        
        # First, list disks and select disks to erase
        disks = select_disks()
        if not disks:
            print("No disks selected. Exiting.")
            return
        
        # Then, get confirmation for each disk
        confirmed_disks = get_disk_confirmations(disks)
        if not confirmed_disks:
            print("No disks confirmed for erasure. Exiting.")
            return
        
        # Finally, choose filesystem and number of passes
        fs_choice = args.filesystem or choose_filesystem()
        passes = args.passes
        use_crypto = args.crypto
        
        print(f"Selected filesystem: {fs_choice}")
        if use_crypto:
            print("Erasure method: Cryptographic erasure")
        else:
            print(f"Erasure method: Standard with {passes} passes")
        
        print("\nAll disks confirmed. Starting operations...\n")
        log_info(f"Starting disk erasure operations on {len(confirmed_disks)} disk(s)")
        
        with ThreadPoolExecutor() as executor:
            # Use our cli_process_disk function with the crypto flag
            futures = [executor.submit(cli_process_disk, disk, fs_choice, passes, use_crypto) for disk in confirmed_disks]
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        completed += 1
                except (RuntimeError, ValueError) as e:
                    log_error(f"Error processing disk: {str(e)}")
        
        print(f"\nCompleted operations on {completed}/{len(confirmed_disks)} disks.")
        log_info(f"Completed operations on {completed}/{len(confirmed_disks)} disks.")
        
    except KeyboardInterrupt:
        log_error("Program terminated by user (Ctrl+C)")
        sys.exit(130)
    except IOError as e:
        log_error(f"I/O error: {str(e)}")
        sys.exit(1)
    except OSError as e:
        log_error(f"OS error: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        log_error(f"Value error: {str(e)}")
        sys.exit(1)
    except SubprocessError as e:
        log_error(f"Subprocess error: {str(e)}")
        sys.exit(1)