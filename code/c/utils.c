#include "utils.h"
#include <stdio.h>
#include <stdlib.h>

int run_command(const char *command) {
    int ret = system(command);
    if (ret != 0) {
        fprintf(stderr, "Command failed: %s\n", command);
        return 0;
    }
    return 1;
}
