#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include "disk_erase.h"
#include "disk_partition.h"
#include "disk_format.h"
#include "utils.h"

#define MAX_DISKS 10

typedef struct {
    char disk[256];
    char fs_choice[16];
} DiskInfo;

void *process_disk(void *args) {
    DiskInfo *info = (DiskInfo *)args;
    int passes = 5; // default passes

    printf("Erasing %s with %d passes...\n", info->disk, passes);
    erase_disk(info->disk, passes);

    printf("Partitioning %s...\n", info->disk);
    partition_disk(info->disk);

    printf("Formatting %s with %s filesystem...\n", info->disk, info->fs_choice);
    format_disk(info->disk, info->fs_choice);

    free(info); // Free allocated memory
    return NULL;
}

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

int main() {
    list_disks();

    char disks[MAX_DISKS][256];
    int disk_count = 0;
    printf("Enter the disks to erase (comma-separated, e.g., sda,sdb): ");
    
    char input[1024];
    fgets(input, sizeof(input), stdin);
    
    int len = strlen(input);
    if (len > 0 && input[len - 1] == '\n') {
        input[len - 1] = '\0';  // Remove newline
    }

    char *token = strtok(input, ",");
    while (token != NULL && disk_count < MAX_DISKS) {
        strncpy(disks[disk_count], token, sizeof(disks[disk_count]) - 1);
        disks[disk_count][sizeof(disks[disk_count]) - 1] = '\0'; // Ensure null termination
        disk_count++;
        token = strtok(NULL, ",");
    }

    char fs_choice[16];
    choose_filesystem(fs_choice, sizeof(fs_choice)); // Get filesystem choice once

    pthread_t threads[disk_count];
    for (int i = 0; i < disk_count; i++) {
        DiskInfo *info = malloc(sizeof(DiskInfo)); // Allocate memory for each thread
        if (!info) {
            fprintf(stderr, "Memory allocation failed!\n");
            exit(EXIT_FAILURE);
        }
        strncpy(info->disk, disks[i], sizeof(info->disk) - 1);
        strncpy(info->fs_choice, fs_choice, sizeof(info->fs_choice) - 1);

        pthread_create(&threads[i], NULL, process_disk, (void *)info);
    }

    for (int i = 0; i < disk_count; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("All operations completed successfully.\n");
    return 0;
}
