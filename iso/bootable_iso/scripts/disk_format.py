from utils import run_command

def format_disk(disk, fs_choice):
    partition = f"/dev/{disk}1"
    if fs_choice == 1:
        print(f"Formatage de {partition} en NTFS...")
        run_command(f"mkfs.ntfs -f {partition}")
    elif fs_choice == 2:
        print(f"Formatage de {partition} en EXT4...")
        run_command(f"mkfs.ext4 {partition}")
    print(f"Partition {partition} formatée avec succès.")
