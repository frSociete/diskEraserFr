# Compiler and flags
CC = gcc
CFLAGS = -std=c11

# Directories
SRC_DIR = src
OBJ_DIR = obj
ELF_DIR = elf

# Source files and object files
SRC_FILES = $(wildcard $(SRC_DIR)/*.c)
OBJ_FILES = $(SRC_FILES:$(SRC_DIR)/%.c=$(OBJ_DIR)/%.o)

# Output executable
EXEC = $(ELF_DIR)/disk_tool

# Default target
all: $(EXEC)

# Rule to create the output ELF
$(EXEC): $(OBJ_FILES)
	@mkdir -p $(ELF_DIR)
	$(CC) $(OBJ_FILES) -o $(EXEC)
	@echo "Build complete: $(EXEC)"

# Rule to compile .c files to .o files
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Clean target to remove the generated files
clean:
	@rm -rf $(OBJ_DIR) $(ELF_DIR)
	@echo "Clean complete."

# Phony targets (not real files)
.PHONY: all clean
