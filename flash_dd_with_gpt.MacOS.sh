#!/bin/zsh
set -e

# =======================
# Color definitions
# =======================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# =======================
# Logging helpers
# =======================
log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

ESUDO=sudo

# =======================
# Image selection
# =======================
show_images() {
    IMAGES=(*.img(N))

    if (( ${#IMAGES[@]} == 0 )); then
        log_error "No .img files found in current directory"
        exit 1
    fi

    log_info "Available image files:"
    local i=1
    for img in "${IMAGES[@]}"; do
        echo " $i. $img ($(du -h "$img" | cut -f1))"
        ((i++))
    done
}

select_image() {
    read "choice?Select image number (1-${#IMAGES[@]}): "

    if (( choice < 1 || choice > ${#IMAGES[@]} )); then
        log_error "Invalid image selection"
        exit 1
    fi

    SELECTED_IMAGE="${IMAGES[$choice]}"
    log_info "Selected image: $SELECTED_IMAGE"
}

# =======================
# Device selection
# =======================
show_devices() {
    log_info "Available disks:"
    diskutil list
    echo
    log_warn "Only select removable disks (USB / SD card)"
}

select_device() {
    while true; do
        read "diskname?Enter target disk (e.g. disk2): "

        [[ "$diskname" =~ ^disk[0-9]+$ ]] || {
            log_error "Invalid disk name"
            continue
        }

        DISK="/dev/$diskname"
        RDISK="/dev/r$diskname"

        diskutil info "$DISK" >/dev/null 2>&1 || {
            log_error "Disk does not exist"
            continue
        }

        # HARD SAFETY BLOCK
        if [[ "$DISK" == "/dev/disk0" ]]; then
            log_error "disk0 is the system disk. Aborting."
            exit 1
        fi

        log_warn "Selected disk:"
        diskutil info "$DISK" | egrep "Device / Media Name|Disk Size|Protocol"

        read "confirm?ALL DATA WILL BE ERASED. Type YES to continue: "
        [[ "$confirm" == "YES" ]] || continue

        break
    done
}

# =======================
# Unmount
# =======================
unmount_disk() {
    log_info "Unmounting disk..."
    $ESUDO diskutil unmountDisk "$DISK"
}

# =======================
# Flash
# =======================
flash_image() {
    log_info "Starting flash process"
    log_info "Image : $SELECTED_IMAGE"
    log_info "Target: $RDISK"
    echo

    $ESUDO dd if="$SELECTED_IMAGE" of="$RDISK" bs=4m status=progress conv=sync
    sync

    log_success "Flash completed successfully"
}

# =======================
# Verify
# =======================
verify_flash() {
    read "verify?Verify written data? (y/n): "
    [[ "$verify" =~ ^[Yy]$ ]] || return

    log_info "Verifying data integrity..."

    IMAGE_SIZE=$(stat -f%z "$SELECTED_IMAGE")

    shasum -a 256 "$SELECTED_IMAGE" | cut -d' ' -f1 > /tmp/img.sha
    $ESUDO dd if="$RDISK" bs=4m count=$((IMAGE_SIZE/4194304)) 2>/dev/null \
        | shasum -a 256 | cut -d' ' -f1 > /tmp/dev.sha

    if cmp /tmp/img.sha /tmp/dev.sha; then
        log_success "Verification successful"
    else
        log_error "Verification FAILED"
    fi

    rm -f /tmp/img.sha /tmp/dev.sha
}

# =======================
# Main
# =======================
main() {
    clear
    echo "=============================================="
    echo " macOS DD Image Flash Script (zsh 5.9)"
    echo "=============================================="
    echo

    show_images
    select_image
    echo

    show_devices
    select_device
    echo

    log_error "!!! FINAL WARNING !!!"
    log_error "This will ERASE ALL DATA on $DISK"
    echo
    read "final?Type 'YES, FLASH IT' to continue: "
    [[ "$final" == "YES, FLASH IT" ]] || {
        log_warn "Operation cancelled"
        exit 0
    }

    unmount_disk
    flash_image
    verify_flash

    log_info "Final disk status:"
    diskutil list "$DISK"

    log_success "All operations completed"
    log_info "You may now safely remove the device"
}

main
