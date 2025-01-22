#include "disk_format.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "utils.h"

void format_disk(const char *disk, const char *fs_choice) {
    char partition[256];
    snprintf(partition, sizeof(partition), "/dev/%s1", disk);

    char command[256];
    if (strcmp(fs_choice, "ntfs") == 0) {
        snprintf(command, sizeof(command), "mkfs.ntfs -f %s", partition);
    } else if (strcmp(fs_choice, "ext4") == 0) {
        snprintf(command, sizeof(command), "mkfs.ext4 %s", partition);
    } else if (strcmp(fs_choice, "vfat") == 0) {
        snprintf(command, sizeof(command), "mkfs.vfat -F 32 %s", partition);
    } else {
        fprintf(stderr, "Unsupported filesystem: %s\n", fs_choice);
        exit(EXIT_FAILURE);
    }

    printf("Formatting %s as %s...\n", partition, fs_choice);
    if (!run_command(command)) {
        fprintf(stderr, "Error formatting partition %s.\n", partition);
        exit(EXIT_FAILURE);
    }

    printf("Partition %s formatted successfully.\n", partition);
}
