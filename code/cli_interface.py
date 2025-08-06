import sys
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from subprocess import CalledProcessError, SubprocessError
from disk_erase import get_disk_serial, is_ssd
from disk_operations import get_active_disk, process_disk
from utils import get_disk_list, choose_filesystem, get_base_disk
from log_handler import log_info, log_error, log_erase_operation, generate_session_pdf, generate_log_file_pdf

# Global session logs for PDF generation
session_logs = []

def add_session_log(message: str) -> None:
    """Add a message to session logs with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    session_logs.append(f"[{timestamp}] {message}")

def print_disk_details(disk):
    """Print detailed information about a disk."""
    try:
        disk_id = get_disk_serial(disk)
        is_disk_ssd = is_ssd(disk)
        active_disks = get_active_disk()
        
        # Get disk information from get_disk_list function including label
        disk_size = "Unknown"
        disk_model = "Unknown"
        disk_label = "No Label"
        available_disks = get_disk_list()
        for available_disk in available_disks:
            if available_disk["device"] == f"/dev/{disk}":
                disk_size = available_disk["size"]
                disk_model = available_disk.get("model", "Unknown")
                disk_label = available_disk.get("label", "No Label")
                break
        
        is_active = False
        if active_disks:
            # get_active_disk() now always returns a list of physical disk names with LVM already resolved
            base_disk = get_base_disk(disk)
            for active_disk in active_disks:
                active_base_disk = get_base_disk(active_disk)
                if base_disk == active_base_disk:
                    is_active = True
                    break
        
        print(f"Disk: /dev/{disk}")
        print(f"  Serial/ID: {disk_id}")
        print(f"  Size: {disk_size}")
        print(f"  Model: {disk_model}")
        print(f"  Label: {disk_label}")
        print(f"  Type: {'Solid_state' if is_disk_ssd else 'Mechanical'}")
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
        available_disks = get_disk_list()
        disk_names = [disk["device"].replace("/dev/", "") for disk in available_disks]

        # Display summary table first
        print("\n" + "=" * 80)
        print("                          AVAILABLE DISKS SUMMARY")
        print("=" * 80)
        print(f"{'Device':<12} {'Size':<8} {'Model':<20} {'Label':<15} {'Type':<12} {'Status'}")
        print("-" * 80)
        
        for disk in disk_names:
            try:
                disk_id = get_disk_serial(disk)
                is_disk_ssd = is_ssd(disk)
                active_disks = get_active_disk()
                
                # Get disk information including label
                disk_size = "Unknown"
                disk_model = "Unknown"
                disk_label = "No Label"
                for available_disk in available_disks:
                    if available_disk["device"] == f"/dev/{disk}":
                        disk_size = available_disk["size"]
                        disk_model = available_disk.get("model", "Unknown")
                        disk_label = available_disk.get("label", "No Label")
                        break
                
                is_active = False
                if active_disks:
                    base_disk = get_base_disk(disk)
                    for active_disk in active_disks:
                        active_base_disk = get_base_disk(active_disk)
                        if base_disk == active_base_disk:
                            is_active = True
                            break
                
                # Truncate long names for table display
                model_display = (disk_model[:18] + "..") if len(disk_model) > 20 else disk_model
                label_display = (disk_label[:13] + "..") if len(disk_label) > 15 else disk_label
                
                disk_type = "SSD" if is_disk_ssd else "HDD"
                status = "ACTIVE!" if is_active else "Safe"
                
                print(f"{disk:<12} {disk_size:<8} {model_display:<20} {label_display:<15} {disk_type:<12} {status}")
                
            except Exception as e:
                print(f"{disk:<12} Error retrieving disk information: {str(e)}")
        
        print("-" * 80)

        # Then iterate over disk_names for detailed view
        print("\n" + "=" * 60)
        print("                    DETAILED DISK INFORMATION")
        print("=" * 60)
        
        for disk in disk_names:
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

def confirm_erasure(disk: str, fs_choice: str, method_description: str) -> bool:
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
            print(f"Filesystem: {fs_choice}")
            print(f"Method: {method_description}")
            print("This operation CANNOT be undone and ALL DATA WILL BE LOST!")
            
            confirmation = input(f"Are you sure you want to erase disk {disk_id}? (yes/no): ").strip().lower()
            if confirmation == "yes":
                # Log the erasure operation before proceeding
                log_erase_operation(disk_id, fs_choice, method_description)
                
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

def get_disk_confirmations(disks: list[str], fs_choice: str, passes: int, use_crypto: bool, zero_fill: bool) -> list[str]:
    """Get confirmation for each disk with operation details."""
    if use_crypto:
        fill_method = "zeros" if zero_fill else "random data"
        method_description = f"cryptographic erasure (filling with {fill_method})"
    else:
        method_description = f"standard {passes}-pass overwrite"
    
    return [disk for disk in disks if confirm_erasure(disk, fs_choice, method_description)]

def print_log_menu() -> None:
    """Display and handle log printing options"""
    while True:
        try:
            print("\n" + "=" * 50)
            print("            LOG PRINTING OPTIONS")
            print("=" * 50)
            print("1. Print Session Log (current session only)")
            print("2. Print Complete Log File (all historical logs)")
            print("3. Return to main menu")
            print("-" * 50)
            
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == "1":
                print_session_log_cli()
            elif choice == "2":
                print_complete_log_cli()
            elif choice == "3":
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\nReturning to main menu...")
            break
        except (IOError, OSError) as e:
            print(f"Error: {str(e)}")

def print_session_log_cli() -> None:
    """Generate and save session log as PDF (CLI version)"""
    try:
        if not session_logs:
            print("No session logs available to print!")
            return
        
        print("Generating session log PDF...")
        pdf_path = generate_session_pdf(session_logs)
        
        print(f"Session log PDF generated successfully!")
        print(f"Saved to: {pdf_path}")
        add_session_log(f"Session log PDF saved to: {pdf_path}")
        
    except Exception as e:
        error_msg = f"Error generating session log PDF: {str(e)}"
        print(error_msg)
        log_error(error_msg)

def print_complete_log_cli() -> None:
    """Generate and save complete log file as PDF (CLI version)"""
    try:
        print("Generating complete log PDF...")
        pdf_path = generate_log_file_pdf()
        
        print(f"Complete log PDF generated successfully!")
        print(f"Saved to: {pdf_path}")
        add_session_log(f"Complete log PDF saved to: {pdf_path}")
        
    except Exception as e:
        error_msg = f"Error generating complete log PDF: {str(e)}"
        print(error_msg)
        log_error(error_msg)

def cli_process_disk(disk, fs_choice, passes, use_crypto=False, zero_fill=False):
    """
    Process a single disk for the CLI interface with status output.
    
    This function wraps the process_disk function from disk_operations.py
    to provide CLI-specific logging and error handling.
    """
    try:
        # Get the disk identifier for better logging
        disk_id = get_disk_serial(disk)
        process_msg = f"Processing disk {disk_id} (/dev/{disk})"
        print(f"\n{process_msg}...")
        add_session_log(process_msg)
        
        # Define a logging function for the CLI
        def log_progress(message):
            print(f"  {message}")
            add_session_log(f"  {message}")
        
        # Indicate if the disk is an SSD and not using crypto
        if is_ssd(disk) and not use_crypto:
            warning_msg = f"WARNING: {disk_id} is an SSD - multiple-pass erasure may not be effective"
            print(f"  {warning_msg}")
            add_session_log(warning_msg)
        
        # Process the disk using the imported function with crypto flag and filling method
        filling_method = "zero" if zero_fill else "random"
        process_disk(disk, fs_choice, passes, use_crypto, log_func=log_progress, crypto_fill=filling_method)
        
        success_msg = f"Successfully completed all operations on disk {disk_id}"
        print(success_msg)
        add_session_log(success_msg)
        return True
    except (CalledProcessError, SubprocessError) as e:
        error_msg = f"Error processing disk /dev/{disk}: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        return False
    except IOError as e:
        error_msg = f"I/O error while processing disk /dev/{disk}: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        return False
    except OSError as e:
        error_msg = f"OS error while processing disk /dev/{disk}: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        return False
    except ValueError as e:
        error_msg = f"Value error while processing disk /dev/{disk}: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        return False
    except KeyboardInterrupt:
        error_msg = f"Disk processing interrupted for /dev/{disk}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        return False

def run_disk_erasure_operation(args):
    """Run the disk erasure operation workflow"""
    try:
        # First, list disks and select disks to erase
        print("List of available disks: ")
        disks = select_disks()
        if not disks:
            print("No disks selected. Returning to main menu.")
            return
        
        # Get operation parameters
        fs_choice = args.filesystem or choose_filesystem()
        passes = args.passes
        use_crypto = args.crypto
        zero_fill = args.zero
        
        print(f"Selected filesystem: {fs_choice}")
        add_session_log(f"Selected filesystem: {fs_choice}")
        
        if use_crypto:
            fill_method = "zeros" if zero_fill else "random data"
            method_msg = f"Erasure method: Cryptographic erasure (filling with {fill_method})"
            print(method_msg)
            add_session_log(method_msg)
        else:
            method_msg = f"Erasure method: Standard with {passes} passes"
            print(method_msg)
            add_session_log(method_msg)
        
        # Then, get confirmation for each disk with detailed operation info
        confirmed_disks = get_disk_confirmations(disks, fs_choice, passes, use_crypto, zero_fill)
        if not confirmed_disks:
            print("No disks confirmed for erasure. Returning to main menu.")
            return
        
        print("\nAll disks confirmed. Starting operations...\n")
        operation_start_msg = f"Starting disk erasure operations on {len(confirmed_disks)} disk(s)"
        log_info(operation_start_msg)
        add_session_log(operation_start_msg)
        
        with ThreadPoolExecutor() as executor:
            # Use our cli_process_disk function with the crypto flag and zero_fill option
            futures = [executor.submit(cli_process_disk, disk, fs_choice, passes, use_crypto, zero_fill) for disk in confirmed_disks]
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        completed += 1
                except (RuntimeError, ValueError) as e:
                    error_msg = f"Error processing disk: {str(e)}"
                    log_error(error_msg)
                    add_session_log(error_msg)
        
        completion_msg = f"Completed operations on {completed}/{len(confirmed_disks)} disks."
        print(f"\n{completion_msg}")
        log_info(completion_msg)
        add_session_log(completion_msg)
        
    except KeyboardInterrupt:
        interrupt_msg = "Disk erasure operation interrupted by user (Ctrl+C)"
        print(f"\n{interrupt_msg}")
        add_session_log(interrupt_msg)
    except Exception as e:
        error_msg = f"Unexpected error during disk erasure operation: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)

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
        
        # Initialize session log
        start_msg = "CLI session started"
        add_session_log(start_msg)
        print(f"Session started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        while True:
            try:
                print("\n" + "=" * 50)
                print("                MAIN MENU")
                print("=" * 50)
                print("1. Start Disk Erasure Operation")
                print("2. Print Log Options")
                print("3. Exit")
                print("-" * 50)
                
                choice = input("Enter your choice (1-3): ").strip()
                
                if choice == "1":
                    # Disk erasure operation
                    run_disk_erasure_operation(args)
                
                elif choice == "2":
                    # Print log options
                    print_log_menu()
                
                elif choice == "3":
                    # Exit
                    exit_msg = "CLI session ended by user"
                    print(f"\n{exit_msg}")
                    add_session_log(exit_msg)
                    log_info(exit_msg)
                    break
                
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")
                    
            except KeyboardInterrupt:
                interrupt_msg = "Main menu operation interrupted by user (Ctrl+C)"
                print(f"\n{interrupt_msg}")
                add_session_log(interrupt_msg)
                continue
                
    except KeyboardInterrupt:
        final_interrupt_msg = "Program terminated by user (Ctrl+C)"
        print(f"\n{final_interrupt_msg}")
        log_error(final_interrupt_msg)
        add_session_log(final_interrupt_msg)
        sys.exit(130)
    except IOError as e:
        error_msg = f"I/O error: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        sys.exit(1)
    except OSError as e:
        error_msg = f"OS error: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        sys.exit(1)
    except ValueError as e:
        error_msg = f"Value error: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        sys.exit(1)
    except SubprocessError as e:
        error_msg = f"Subprocess error: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        sys.exit(1)
    finally:
        # Ensure final session log entry
        final_msg = "CLI application terminated"
        add_session_log(final_msg)