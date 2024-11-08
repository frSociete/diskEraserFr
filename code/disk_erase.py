from utils import run_command

def erase_disk(disk):
    confirm = input(f"Are you sure you want to securely erase {disk}? This cannot be undone. (y/n): ")
    if confirm.lower() == 'y':
        print(f"Erasing {disk} with multiple random data passes and a final zero pass for security...")
        run_command(f"shred -v -n 3 -z /dev/{disk}")
        print(f"Disk {disk} successfully erased with random data.")
    else:
        print("Operation cancelled.")
