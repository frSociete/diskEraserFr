#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include "disk_erase.h"
#include "utils.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int is_ssd(const char *device) {
    char path[256];
    snprintf(path, sizeof(path), "/sys/block/%s/queue/rotational", device);

    FILE *file = fopen(path, "r");
    if (!file) {
        perror(path);
        return -1;
    }

    char buffer[10];
    if (!fgets(buffer, sizeof(buffer), file)) {
        perror("Error reading from file");
        fclose(file);
        return -1;
    }

    fclose(file);

    // Trim newline character
    buffer[strcspn(buffer, "\n")] = 0;

    // Convert to integer and check rotational value
    return atoi(buffer) == 0 ? 0 : 1;
}


void erase_disk(const char *device, int passes) {
    if (!is_ssd(device)) {
        printf("Warning: %s appears to be an SSD. Use `hdparm` for secure erase.\n", device);
        return;
    }

    printf("Erasing %s using shred with %d passes...\n", device, passes);

    for (int i = 1; i <= passes; i++) {
        printf("Pass %d of %d is being processed...\n", i, passes);
        char cmd[256];
        snprintf(cmd, sizeof(cmd), "shred -n 1 -z /dev/%s", device);
        if (system(cmd) != 0) {
            perror("Error executing shred command");
            exit(1);
        }
    }

    printf("Wiping partition table of %s using dd...\n", device);
    if (system("dd if=/dev/zero of=/dev/device bs=1M count=10") != 0) {
        perror("Error executing dd command");
        exit(1);
    }

    printf("Disk %s successfully erased.\n", device);
}
