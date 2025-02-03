#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "disk_partition.h"
#include "utils.h"

void partition_disk(const char *disk) {
    printf("Partitioning disk %s...\n", disk);

    char cmd[256];
    snprintf(cmd, sizeof(cmd), "parted /dev/%s --script mklabel gpt", disk);
    if (system(cmd) != 0) {
        perror("Error creating partition label");
        exit(1);
    }

    snprintf(cmd, sizeof(cmd), "parted /dev/%s --script mkpart primary 0%% 100%%", disk);
    if (system(cmd) != 0) {
        perror("Error creating partition");
        exit(1);
    }

    printf("Disk %s partitioned successfully.\n", disk);
}
