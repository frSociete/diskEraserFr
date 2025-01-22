import subprocess

def run_command(command_list):
    try:
        result = subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(f"Error while executing the command: {' '.join(command_list)}")
        print(e.stderr.decode('utf-8'))
        return None

def list_disks():
    print("List of available disks:")
    try:
        output = run_command(["lsblk", "-d", "-o", "NAME,SIZE,TYPE"])
        if output:
            print(output)
        else:
            print("No disks detected. Ensure the program is run with appropriate permissions.")
    except Exception as e:
        print(f"An error occurred while retrieving disks: {e}")
