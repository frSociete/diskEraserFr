from utils import run_command

def partition_disk(disk):
    print(f"Partitioning disk {disk}...")
    run_command(["parted", f"/dev/{disk}", "--script", "mklabel", "gpt"])
    run_command(["parted", f"/dev/{disk}", "--script", "mkpart", "primary", "0%", "100%"])
    print(f"Disque {disk} partitionné avec succès.")
