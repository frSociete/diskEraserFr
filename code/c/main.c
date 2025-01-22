#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "disk_erase.h"
#include "disk_partition.h"
#include "disk_format.h"
#include "utils.h"

// Function to list available disks
void list_disks() {
    printf("Available disks:\n");
    run_command("lsblk -d -o NAME,SIZE,TYPE");
}

// Function to get user input for disk selection
void select_disk(char *disk, size_t size) {
    list_disks();
    printf("\nEnter the disk to erase (e.g., sda): ");
    if (!fgets(disk, size, stdin)) {
        fprintf(stderr, "Error reading input.\n");
        exit(EXIT_FAILURE);
    }
    disk[strcspn(disk, "\n")] = '\0'; // Remove newline character
}

// Function to choose filesystem
void choose_filesystem(char *fs_choice, size_t size) {
    int choice;
    printf("\nChoose a filesystem to format the disks:\n");
    printf("1. NTFS\n");
    printf("2. EXT4\n");
    printf("3. VFAT\n");
    printf("Enter your choice (1, 2, or 3): ");
    if (scanf("%d", &choice) != 1) {
        fprintf(stderr, "Invalid input.\n");
        exit(EXIT_FAILURE);
    }

    switch (choice) {
        case 1:
            strncpy(fs_choice, "ntfs", size);
            break;
        case 2:
            strncpy(fs_choice, "ext4", size);
            break;
        case 3:
            strncpy(fs_choice, "vfat", size);
            break;
        default:
            fprintf(stderr, "Invalid choice.\n");
            exit(EXIT_FAILURE);
    }
}

// Main process for disk operations
void process_disk_interactive() {
    char disk[256];
    char fs_choice[16];
    int passes;

    select_disk(disk, sizeof(disk));
    choose_filesystem(fs_choice, sizeof(fs_choice));
    passes = 6;

    printf("\nStarting operations on disk: %s\n", disk);

    erase_disk(disk, passes);
    partition_disk(disk);
    format_disk(disk, fs_choice);

    printf("\nCompleted operations on disk: %s\n", disk);
}

int main() {
    if (geteuid() != 0) {
        fprintf(stderr, "This program must be run as root.\n");
        return EXIT_FAILURE;
    }

    process_disk_interactive();

    return EXIT_SUCCESS;
}
