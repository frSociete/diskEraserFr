#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "disk_format.h"
#include "utils.h"

void format_disk(const char *disk, const char *fs_choice) {
    char partition[256];
    snprintf(partition, sizeof(partition), "/dev/%s1", disk);

    char cmd[256];
    if (strcmp(fs_choice, "ntfs") == 0) {
        printf("Formatting %s as NTFS...\n", partition);
        snprintf(cmd, sizeof(cmd), "mkfs.ntfs -f %s", partition);
    } else if (strcmp(fs_choice, "ext4") == 0) {
        printf("Formatting %s as EXT4...\n", partition);
        snprintf(cmd, sizeof(cmd), "mkfs.ext4 %s", partition);
    } else if (strcmp(fs_choice, "vfat") == 0) {
        printf("Formatting %s as VFAT...\n", partition);
        snprintf(cmd, sizeof(cmd), "mkfs.vfat -F 32 %s", partition);
    }

    if (system(cmd) != 0) {
        perror("Error executing format command");
        exit(1);
    }

    printf("Partition %s formatted successfully.\n", partition);
}
