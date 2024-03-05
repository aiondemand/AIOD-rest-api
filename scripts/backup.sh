#!/bin/bash

if [ "$ENV_MODE" != "testing" ]; then
    SCRIPT_PATH="$(readlink -f "$0")"
    SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

    cd $SCRIPT_DIR/..
    source .env
fi

DATA_PATH=$(realpath "$DATA_PATH")
BACKUP_PATH=$(realpath "$BACKUP_PATH")

if [ $# -ne 2 ]; then
  echo "Usage: $0 <data to backup:str> <cycle length:int>"
  echo ""
  echo "Perform incremental backups based on a cycle length."
  echo "A full backup (level 0) is created initially, followed by incremental backups (level 1, 2, ...)."
  echo "These incremental backups contain only the changed files since the last backup."
  echo "<data to backup> is the name of the folder in ${DATA_PATH} that you want to backup,"
  echo "and the <cycle length> determines the maximum number of incremental backups before starting a new cycle with a fresh level 0 backup."
  echo "For more details on incremental backups, visit: https://www.gnu.org/software/tar/manual/html_section/Incremental-Dumps.html"
  exit 1
fi

data_to_backup=$1
cycle_length=$2

check_file_or_dir () {
    path=$1
    if [ ! -d "$path" ] && [ ! -f "$path" ]; then
        echo $(date -u) "Error: Path does not exist: $path"
        echo $(date -u) "Operation aborted!"
        exit 1
    fi
}
check_file_or_dir "${DATA_PATH}/${data_to_backup}"
check_file_or_dir "$BACKUP_PATH"

echo $(date -u) "Backup routine to ${data_to_backup} starting..."

cd "${DATA_PATH}"
path_to_data="./${data_to_backup}"
parent_dir="${BACKUP_PATH}/${data_to_backup}"

if [ -z "$(ls -A $parent_dir)" ]; then
    backup_dir="${parent_dir}/${data_to_backup}_0"
    echo $(date -u) "-> Creating backup directory..."
    mkdir -p "$backup_dir"
    level=0
else
    backup_dir=$(find "$parent_dir" -type d -name "${data_to_backup}*" | sort | tail -n 1)
    level=$(ls "$backup_dir" | grep -c "${data_to_backup}")
    level=$((level - 1))
    if [ $level -le 0 ]; then
        echo $(date -u) "-> Level 0 might be corrupted! Backing up from level 0."
        level=0
    elif [ "$level" -ge "$cycle_length" ]; then
        echo $(date -u) "-> Backup cycle completed, starting a new one."
        last_backup_label="${backup_dir##*_}"
        backup_dir="${parent_dir}/${data_to_backup}_$((last_backup_label + 1))"
        mkdir "$backup_dir"
        level=0
    fi
fi

backup_file="${backup_dir}/${data_to_backup}${level}.tar.gz"
snapshot_file="${backup_dir}/${data_to_backup}.snar"

tar -czf "$backup_file" --listed-incremental="$snapshot_file" "$path_to_data"

echo $(date -u) "-> Files from ${data_to_backup} backed up."
echo $(date -u) "   ${DATA_PATH}/${data_to_backup} -----> ${parent_dir}"
echo $(date -u) "Done!"