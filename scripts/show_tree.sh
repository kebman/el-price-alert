#!/usr/bin/env bash
# scripts/show-tree.sh

set -euo pipefail

# Configuration
readonly DEFAULT_IGNORE_DIRS=(".git" "node_modules")
readonly BOLD=$(tput bold 2>/dev/null || echo "")
readonly RESET=$(tput sgr0 2>/dev/null || echo "")

# Parse arguments
parse_args() {
    local start_dir="${1:-.}"
    shift || true
    
    local ignore_dirs=("${DEFAULT_IGNORE_DIRS[@]}" "$@")
    
    # Create ignore pattern more efficiently
    local IFS="|"
    local ignore_pattern="^(${ignore_dirs[*]})$"
    
    printf '%s\n%s\n' "$start_dir" "$ignore_pattern"
}

# Format file size
format_size() {
    local size="$1"
    
    # Use numfmt if available, otherwise simple fallback
    if command -v numfmt >/dev/null 2>&1; then
        numfmt --to=iec --suffix=B "$size" 2>/dev/null || echo "${size}B"
    else
        # Simple fallback for systems without numfmt
        if ((size >= 1073741824)); then
            printf "%.1fG\n" "$(bc -l <<< "$size/1073741824" 2>/dev/null || echo "$size")"
        elif ((size >= 1048576)); then
            printf "%.1fM\n" "$(bc -l <<< "$size/1048576" 2>/dev/null || echo "$size")"
        elif ((size >= 1024)); then
            printf "%.1fK\n" "$(bc -l <<< "$size/1024" 2>/dev/null || echo "$size")"
        else
            printf "%dB\n" "$size"
        fi
    fi
}

# Get directory size efficiently
get_dir_size() {
    local dir="$1"
    
    # Use du with timeout to avoid hanging on problematic directories
    timeout 5s du -sb "$dir" 2>/dev/null | awk '{print $1}' || echo "0"
}

# Get file size
get_file_size() {
    local file="$1"
    
    if [[ -r "$file" ]]; then
        stat --format="%s" "$file" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# Build items array more efficiently
build_items_array() {
    local dir="$1"
    local ignore_regex="$2"
    local -n items_ref=$3
    
    # Clear the array
    items_ref=()
    
    # Use a more efficient approach with find
    while IFS= read -r -d '' item; do
        local base
        base=$(basename "$item")
        
        # Skip ignored directories
        [[ "$base" =~ $ignore_regex ]] && continue
        
        items_ref+=("$item")
    done < <(find "$dir" -mindepth 1 -maxdepth 1 -print0 2>/dev/null | sort -z)
}

# Main tree drawing function
tree_draw() {
    local dir="$1"
    local prefix="$2"
    local ignore_regex="$3"
    local items=()
    
    # Build items array
    build_items_array "$dir" "$ignore_regex" items
    
    local total=${#items[@]}
    local i
    
    for i in "${!items[@]}"; do
        local item="${items[$i]}"
        local base
        base=$(basename "$item")
        
        local is_last=$((i == total - 1))
        local treechar size size_fmt
        
        if [[ $is_last -eq 1 ]]; then
            treechar="└──"
        else
            treechar="├──"
        fi
        
        if [[ -d "$item" ]]; then
            size=$(get_dir_size "$item")
            size_fmt=$(format_size "$size")
            
            printf '%s%s %s%s/%s (%s)\n' \
                "$prefix" "$treechar" "$BOLD" "$base" "$RESET" "$size_fmt"
            
            # Recurse into directory
            local newprefix
            if [[ $is_last -eq 1 ]]; then
                newprefix="$prefix    "
            else
                newprefix="$prefix│   "
            fi
            
            tree_draw "$item" "$newprefix" "$ignore_regex"
        else
            size=$(get_file_size "$item")
            size_fmt=$(format_size "$size")
            
            printf '%s%s %s (%s)\n' \
                "$prefix" "$treechar" "$base" "$size_fmt"
        fi
    done
}

# Validate directory
validate_directory() {
    local dir="$1"
    
    if [[ ! -d "$dir" ]]; then
        printf 'Error: "%s" is not a directory\n' "$dir" >&2
        return 1
    fi
    
    if [[ ! -r "$dir" ]]; then
        printf 'Error: Cannot read directory "%s"\n' "$dir" >&2
        return 1
    fi
    
    return 0
}

# Main function
main() {
    local start_dir ignore_pattern
    
    # Parse arguments
    {
        read -r start_dir
        read -r ignore_pattern
    } < <(parse_args "$@")
    
    # Validate directory
    validate_directory "$start_dir" || exit 1
    
    # Print header
    printf 'Directory tree for: %s\n' "$(realpath "$start_dir" 2>/dev/null || echo "$start_dir")"
    
    # Draw tree
    tree_draw "$start_dir" "" "$ignore_pattern"
}

# Error handling
error_handler() {
    local line_no=$1
    printf 'Error occurred on line %d\n' "$line_no" >&2
    exit 1
}

trap 'error_handler $LINENO' ERR

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi