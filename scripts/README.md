# Scripts README.md

This directory contains a collection of scripts designed to manage backups, restorations, and database interactions for the service. Below is a detailed description of each script and its intended usage.
Unless noted otherwise, all scripts should be run without arguments while the AIoD docker containers are running (i.e., `docker compose up`).

## Script Descriptions

## `up.sh`
Shorthand for `docker compose up -d` which takes as arguments any profile names you also want to up.
Will automatically specify to use both `.env` and `override.env` and also mount local source code if `AIOD_MOUNT` is set.

## `down.sh`
Shorthand to bring down all docker containers regardless of profile.

### `clean.sh`

> [!WARNING]
> This deletes all the content in the data/ directory!
- **Purpose**: This convenience script reverts the development environment back to a clean state, including resetting the database.


### `database-connect.sh`

- **Purpose**: Start an interactive MySQL client that connects to the AIoD SQL server. 

### `mysql_dump.sh`

- **Purpose**: Exports a logical backup of the `aiod` database from the SQL server and extracts it to `data/path/mysql_dump`.

### `mysql_restore.sh`

- **Purpose**: Uses the `backup.sql` exported by `mysql_dump.sh` to restore the MySQL database.

### `realm_export.sh`

- **Purpose**: Exports the realm information from the Keycloak service.

### `backup.sh`

- **Purpose**: Creates incremental backups of specified data.
- **Usage**:
  ```bash
  ./backup.sh <data to backup> <cycle length>
  ```
  - `<data to backup>`: Name of the folder in `${DATA_PATH}` you wish to back up.
  - `<cycle length>`: Determines the maximum number of incremental backups before starting a new cycle with a fresh level 0 backup.

  Incremental backups start with a full backup (level 0), followed by backups (level 1, 2, ...) that contain only the changed files since the last backup.

  For more details on incremental backups, visit: [GNU Tar Manual - Incremental Dumps](https://www.gnu.org/software/tar/manual/html_section/Incremental-Dumps.html)

### `restore.sh`

- **Purpose**: Used to restore data from the incremental backups produced by `backup.sh`.
- **Usage**:
  ```bash
  ./restore.sh <data to restore> <cycle label> [--level|-l <level>]
  ```
  - `<data to restore>`: Name of the data folder to restore (e.g., "connectors").
  - `<cycle label>`: Corresponds to the label of the backup directory inside the backup path.
  - `--level|-l <level>`: (Optional) Specifies a cycle level to restore from a specific incremental backup within a cycle. If omitted, all levels within the cycle will be restored.

  For more details on the structure and restoration process of incremental backups, visit: [GNU Tar Manual - Incremental Dumps](https://www.gnu.org/software/tar/manual/html_section/Incremental-Dumps.html)

## Backup Procedure

Incremental backups can be scheduled with `cron` to execute `backup.sh` periodically for any data folder. However, for the MySQL and Keycloak services, it's recommended to use the auxiliary scripts (`mysql_dump.sh` and `realm_export.sh`) to export the databases from these services first. This approach helps avoid concurrency issues. These scripts will store the exported files to a designated folder in `data/path`. Then, run `backup.sh`, passing the name of the folder in `data/path` that you want to back up. The process can be scheduled with `crontab`.

### Usage Example

To schedule weekly (cycle length: 7) backups to run everyday at 2 am of the MySQL DB, set a cron file as follows: 

```cron
0 2 * * * bash path/to/scripts/mysql_dump.sh >> cron.log 2>&1
15 2 * * * bash path/to/scripts/backup.sh mysql_dump 7 >> cron.log 2>&1
```

To restore the it from the 2nd (level 1) day of the 3rd week (cycle 2) you can run manually first the _restore.sh_ script followed by the _mysql_restore.sh_ script.

```bash
>> bash path/to/scripts/restore.sh mysql_dump 2 -l 1
>> bash path/to/scripts/mysql_restore.sh
```