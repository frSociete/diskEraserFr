#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "disk_erase.h"
#include "disk_partition.h"
#include "disk_format.h"
#include "utils.h"
#include <pthread.h>

#define MAX_DISKS 10

void *process_disk(void *args) {
    char *disk = (char *)args;
    char fs_choice[16];
    int passes = 5; // default passes

    erase_disk(disk, passes);
    partition_disk(disk);
    format_disk(disk, fs_choice);

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
    input[len-1] = '\0';
    fprintf(stderr, "input: %s\n", input);

    char *token = strtok(input, ",");
    while (token != NULL && disk_count < MAX_DISKS) {
        strncpy(disks[disk_count], token, sizeof(disks[disk_count]) - 1);
        disk_count++;
        token = strtok(NULL, ",");
    }

    pthread_t threads[disk_count];
    for (int i = 0; i < disk_count; i++) {
        pthread_create(&threads[i], NULL, process_disk, (void *)disks[i]);
    }

    for (int i = 0; i < disk_count; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("All operations completed successfully.\n");
    return 0;
}
