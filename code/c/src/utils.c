#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "utils.h"

void run_command(const char *command) {
    int result = system(command);
    if (result != 0) {
        perror("Command execution failed");
        exit(1);
    }
}

void list_disks() {
    printf("List of available disks:\n");
    const char *cmd = "lsblk -d -o NAME,SIZE,TYPE";
    run_command(cmd);
}
