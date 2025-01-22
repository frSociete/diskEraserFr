#include "disk_partition.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "utils.h"

void partition_disk(const char *disk) {
    printf("Partitioning disk %s...\n", disk);
    char command1[256];
    char command2[256];

    snprintf(command1, sizeof(command1), "parted /dev/%s --script mklabel gpt", disk);
    snprintf(command2, sizeof(command2), "parted /dev/%s --script mkpart primary 0%% 100%%", disk);

    if (!run_command(command1) || !run_command(command2)) {
        fprintf(stderr, "Error partitioning disk %s.\n", disk);
        exit(EXIT_FAILURE);
    }

    printf("Disk %s partitioned successfully.\n", disk);
}
