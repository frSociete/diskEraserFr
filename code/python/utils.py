import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_command(command_list):
    try:
        result = subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8').strip()
    except FileNotFoundError:
        logging.info(f"Error: Command not found: {' '.join(command_list)}")
    except subprocess.CalledProcessError:
        logging.info(f"Error: Command execution failed: {' '.join(command_list)}")

def list_disks():
    logging.info("List of available disks:")
    try:
        output = run_command(["lsblk", "-d", "-o", "NAME,SIZE,TYPE"])
        if output:
            logging.info(output)
        else:
            logging.info("No disks detected. Ensure the program is run with appropriate permissions.")
    except FileNotFoundError:
        logging.info("Error: `lsblk` command not found. Install `util-linux` package.")
    except subprocess.CalledProcessError:
        logging.info("Error: Failed to retrieve disk information.")
