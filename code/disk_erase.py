import os

def write_random_data(device, passes=4):
    """
    Overwrite the entire device with random data for the specified number of passes.
    """
    block_size = 4096
    try:
        with open(f"/dev/{device}", "wb") as disk:
            disk_size = os.lseek(disk.fileno(), 0, os.SEEK_END)
            os.lseek(disk.fileno(), 0, os.SEEK_SET)
            for pass_num in range(passes):
                print(f"Writing random data pass {pass_num + 1} to {device}...")
                written = 0
                while written < disk_size:
                    remaining = disk_size - written
                    to_write = min(block_size, remaining)
                    disk.write(os.urandom(to_write))
                    written += to_write
                disk.flush()
                os.lseek(disk.fileno(), 0, os.SEEK_SET)
    except Exception as e:
        print(f"Error while writing random data to {device}: {e}")
        raise

def write_zero_data(device):
    """
    Overwrite the entire device with zeros.
    """
    block_size = 4096
    try:
        with open(f"/dev/{device}", "wb") as disk:
            disk_size = os.lseek(disk.fileno(), 0, os.SEEK_END)
            os.lseek(disk.fileno(), 0, os.SEEK_SET)

            print(f"Writing final zero pass to {device}...")
            written = 0
            while written < disk_size:
                remaining = disk_size - written
                to_write = min(block_size, remaining)
                disk.write(b"\x00" * to_write)
                written += to_write
            disk.flush()
    except Exception as e:
        print(f"Error while writing zero data to {device}: {e}")
        raise

def erase_disk(disk):
    """
    Securely erase the entire disk by overwriting it with random data and zeros.
    """
    try:
        print(f"Erasing {disk} with multiple random data passes and a final zero pass for security...")

        write_random_data(disk)

        write_zero_data(disk)

        print(f"Disk {disk} successfully erased with random data and zeros.")
    except Exception as e:
        print(f"Failed to erase disk {disk}: {e}")
