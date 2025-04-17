import subprocess
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_command(command_list: list[str]) -> str:
    try:
        result = subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8').strip()
    except FileNotFoundError:
        logging.error(f"Error: Command not found: {' '.join(command_list)}")
        sys.exit(2)
    except subprocess.CalledProcessError:
        logging.error(f"Error: Command execution failed: {' '.join(command_list)}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.error("Operation interrupted by user (Ctrl+C)")
        print("\nOperation interrupted by user (Ctrl+C)")
        sys.exit(130)  # Standard exit code for SIGINT

def list_disks() -> str:
    """
    Get a raw string output of available disks using lsblk command.
    Returns the output of the lsblk command or an empty string if no disks found.
    """
    print("List of available disks:")
    try:
        # Use more explicit column specification with -o option and -n to skip header
        output = run_command(["lsblk", "-d", "-o", "NAME,SIZE,TYPE,MODEL", "-n"])
        if output:
            return output
        else:
            # Fallback to a simpler command if the first one returned no results
            output = run_command(["lsblk", "-d", "-o", "NAME", "-n"])
            if output:
                logging.info(output)
                return output
            else:
                logging.info("No disks detected. Ensure the program is run with appropriate permissions.")
                return ""
    except FileNotFoundError:
        logging.error("Error: `lsblk` command not found. Install `util-linux` package.")
        sys.exit(2)
    except subprocess.CalledProcessError:
        logging.error("Error: Failed to retrieve disk information.")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.error("Disk listing interrupted by user (Ctrl+C)")
        print("\nDisk listing interrupted by user (Ctrl+C)")
        sys.exit(130)

def get_disk_list() -> list[dict]:
    """
    Get list of available disks as structured data.
    Returns a list of dictionaries with disk information.
    Each dictionary contains: 'device', 'size', and 'model'.
    """
    try:
        # Use list_disks function to get raw output
        output = list_disks()
        
        if not output:
            logging.info("No disks found.")
            return []
        
        # Parse the output from lsblk command
        disks = []
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
                
            # Split the line but preserve the model name which might contain spaces
            parts = line.strip().split(maxsplit=3)
            device = parts[0]
            
            # Ensure we have at least NAME and SIZE
            if len(parts) >= 2:
                size = parts[1]
                
                # MODEL may be missing, set to "Unknown" if it is
                model = parts[3] if len(parts) > 3 else "Unknown"
                
                disks.append({
                    "device": f"/dev/{device}",
                    "size": size,
                    "model": model
                })
        
        return disks
    except FileNotFoundError as e:
        logging.error(f"Error: Command not found: {str(e)}")
        return []
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing command: {str(e)}")
        return []
    except (IndexError, ValueError) as e:
        logging.error(f"Error parsing disk information: {str(e)}")
        return []
    except KeyboardInterrupt:
        logging.error("Disk listing interrupted by user")
        return []

def choose_filesystem() -> str:
    """
    Prompt the user to choose a filesystem.
    """
    while True:
        try:
            print("Choose a filesystem to format the disks:")
            print("1. NTFS")
            print("2. EXT4")
            print("3. VFAT")
            choice = input("Enter your choice (1, 2, or 3): ").strip()

            if choice == "1":
                return "ntfs"
            elif choice == "2":
                return "ext4"
            elif choice == "3":
                return "vfat"
            else:
                logging.error("Invalid choice. Please select a correct option.")
        except KeyboardInterrupt:
            logging.error("Filesystem selection interrupted by user (Ctrl+C)")
            print("\nFilesystem selection interrupted by user (Ctrl+C)")
            sys.exit(130)