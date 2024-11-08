from utils import run_command

def partition_disk(disk):
    print(f"Partitionnement du disque {disk}...")
    run_command(f"parted /dev/{disk} --script mklabel gpt")
    run_command(f"parted /dev/{disk} --script mkpart primary 0% 100%")
    print(f"Disque {disk} partitionné avec succès.")
