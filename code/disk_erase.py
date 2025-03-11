import subprocess
import logging
import sys
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_disk_serial(device: str) -> str:
    """
    Get a stable disk identifier using udevadm to extract WWN or serial number from an unmounted device.
    """
    try:
        # Try getting the WWN (World Wide Name) directly from udevadm
        output = subprocess.run(
            ["udevadm", "info", "--query=property", f"--name=/dev/{device}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).stdout.decode()

        # Look for WWN in the udevadm output
        wwn_match = re.search(r'ID_WWN=(\S+)', output)
        if wwn_match:
            return wwn_match.group(1)

        # If WWN not found, fall back to the serial number
        serial_match = re.search(r'ID_SERIAL_SHORT=(\S+)', output)
        if serial_match:
            return serial_match.group(1)
        
        # Get the model as a fallback if serial is not available
        model_match = re.search(r'ID_MODEL=(\S+)', output)
        if model_match:
            return f"{model_match.group(1)}_{device}"
            
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"Error occurred while querying {device}: {e}")
    except KeyboardInterrupt:
        logging.error("Disk identification interrupted by user (Ctrl+C)")
        print("\nDisk identification interrupted by user (Ctrl+C)")
        sys.exit(130)

    # If all else fails, return a default identifier
    return f"UNKNOWN_{device}"

def is_ssd(device: str) -> bool:
    try:
        output = subprocess.run(
            ["cat", f"/sys/block/{device}/queue/rotational"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return output.stdout.decode().strip() == "0"
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        logging.warning(f"SSD check failed for {device}: {e}")
        # Don't exit, just return False as fallback
        return False
    except KeyboardInterrupt:
        logging.error("SSD check interrupted by user (Ctrl+C)")
        print("\nSSD check interrupted by user (Ctrl+C)")
        sys.exit(130)

def erase_disk_hdd(device: str, passes: int, log_func=None) -> str:
    try:
        # Type-casting arguments to ensure correct types
        device = str(device)
        passes = int(passes)

        # Get stable disk identifier before erasure
        disk_serial = get_disk_serial(device)

        if is_ssd(device):
            logging.warning(f"Warning: {device} appears to be an SSD. Multiple passes may not be effective.")
            # Continue with erasure instead of returning

        logging.info(f"Erasing {device} using shred with {passes} passes...")
        # Also log to GUI if log_func is provided
        if log_func:
            log_func(f"Erasing {device} using shred with {passes} passes...")
        
        # Create a subprocess with stdout piped to capture shred output
        shred_process = subprocess.Popen(
            ["shred", "-n", f"{passes}", "-v", f"/dev/{device}"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            universal_newlines=True
        )

        # Read output in real-time
        while True:
            try:
                output = shred_process.stdout.readline()
                if output == '' and shred_process.poll() is not None:
                    break
                if output:
                    # If a log function is provided (like in GUI), use it
                    # Otherwise, print to stdout
                    if log_func:
                        log_func(output.strip())
                    else:
                        print(output.strip())
            except KeyboardInterrupt:
                # Terminate the shred process if user interrupts
                shred_process.terminate()
                logging.error("Disk erasure interrupted by user (Ctrl+C)")
                print("\nDisk erasure interrupted by user (Ctrl+C)")
                sys.exit(130)

        # Check return code
        if shred_process.returncode != 0:
            raise subprocess.CalledProcessError(shred_process.returncode, "shred")

        # Log partition table wiping to both log file and GUI
        wipe_message = f"Wiping partition table of {device} using dd..."
        logging.info(wipe_message)
        if log_func:
            log_func(wipe_message)
            
        # Run dd command
        subprocess.run(["dd", "if=/dev/zero", f"of=/dev/{device}", "bs=1M", "count=10"], check=True)

        # Log success message to both log file and GUI
        success_message = f"Disk {device} successfully erased."
        logging.info(success_message)
        if log_func:
            log_func(success_message)
            
        return disk_serial
    except FileNotFoundError:
        error_message = "Error: Required command not found."
        logging.error(error_message)
        if log_func:
            log_func(error_message)
        sys.exit(2)
    except subprocess.CalledProcessError as e:
        error_message = f"Error: Failed to erase {device}: {e}"
        logging.error(error_message)
        if log_func:
            log_func(error_message)
        sys.exit(1)
    except KeyboardInterrupt:
        error_message = "Disk erasure interrupted by user (Ctrl+C)"
        logging.error(error_message)
        if log_func:
            log_func(error_message)
        print(f"\n{error_message}")
        sys.exit(130)