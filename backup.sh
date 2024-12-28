#!/bin/bash

# === Configuration ===
BACKUP_DIR="/home/debian/homelab/"  # Directory to back up
ARCHIVE_NAME="/home/debian/homelab_backup_$(date +%d:%m:%Y-%H:%M:%S).7z"  # Archive name with timestamp
REMOTE_DEST="origin:Backups/homelab"  # Remote destination for rclone
LOG_FILE=/home/debian/homelab_backup_job.log  # Log file location
DOCKER_STOP_TIMEOUT=30  # Timeout in seconds for stopping Docker containers
PRIMARY_CONTAINER="qbittorrentvpn"  # Container to start first

# Ensure the log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# === Functions ===

# Logging function
log_message() {
    local MSG="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $MSG" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    log_message "Error: $1"
    exit 1
}

# Stop Docker containers
stop_docker_containers() {
    log_message "Stopping all Docker containers..."
    docker stop --time "$DOCKER_STOP_TIMEOUT" $(docker ps -q) || handle_error "Failed to stop Docker containers."
    log_message "All Docker containers stopped successfully."
}

# Start a specific Docker container and wait until it's running
start_primary_container() {
    log_message "Starting primary container: $PRIMARY_CONTAINER..."
    docker start "$PRIMARY_CONTAINER" || handle_error "Failed to start $PRIMARY_CONTAINER."
    
    log_message "Waiting for $PRIMARY_CONTAINER to be running..."
    while true; do
        STATUS=$(docker inspect -f '{{.State.Running}}' "$PRIMARY_CONTAINER")
        if [ "$STATUS" == "true" ]; then
            log_message "$PRIMARY_CONTAINER is running."
            break
        fi
        sleep 2
    done
}

# Start remaining Docker containers
start_remaining_containers() {
    log_message "Starting remaining Docker containers..."
    for CONTAINER in $(docker ps -aq --filter "name!=$PRIMARY_CONTAINER"); do
        docker start "$CONTAINER" || log_message "Failed to start container $CONTAINER. Continuing..."
    done
    log_message "Remaining Docker containers started successfully."
}

# Compress directory
compress_directory() {
    log_message "Compressing backup directory..."
    7z a $ARCHIVE_NAME $BACKUP_DIR -x!/home/debian/homelab/jellyfin/container_data/jellyfin/cache/* || handle_error "Failed to compress directory."
    log_message "Folder compressed successfully into $ARCHIVE_NAME."
}

# Upload to remote
upload_backup() {
    log_message "Uploading backup to remote destination..."
    rclone copy "$ARCHIVE_NAME" "$REMOTE_DEST" || handle_error "Failed to upload backup with rclone."
    log_message "Backup uploaded successfully to $REMOTE_DEST."
}

# Clean up local archive
cleanup_local() {
    log_message "Cleaning up local backup archive..."
    rm -f "$ARCHIVE_NAME" || handle_error "Failed to remove local backup archive."
    log_message "Local backup archive removed successfully."
}

# === Main Script ===

# Ensure script is run as root
if [[ $EUID -ne 0 ]]; then
    handle_error "This script must be run as root or with sudo."
fi

# Create log file directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

log_message "Starting backup process..."

# Stop Docker containers
stop_docker_containers

# Compress backup directory
compress_directory

# Upload backup to remote
upload_backup

# Start primary container
start_primary_container

# Start remaining containers
start_remaining_containers

# Clean up local archive
cleanup_local

log_message "Backup process completed successfully."
exit 0
