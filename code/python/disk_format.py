from utils import run_command

def format_disk(disk, fs_choice):
    partition = f"/dev/{disk}1"
    if fs_choice == "ntfs":
        print(f"Formatting {partition} as NTFS...")
        run_command(["mkfs.ntfs", "-f", partition])
    elif fs_choice == "ext4":
        print(f"Formatting {partition} as EXT4...")
        run_command(["mkfs.ext4", partition])
    elif fs_choice == "vfat":
        print(f"Formatting {partition} as VFAT...")
        run_command(["mkfs.vfat", "-F", "32", partition])
    print(f"Partition {partition} formatted successfully.")
