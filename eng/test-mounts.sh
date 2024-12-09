#!/usr/bin/env bash
set -xeuo pipefail
IFS=$'\n\t'

print_to_workflow() {
    if [[ -n ${GITHUB_STEP_SUMMARY} ]]; then
        echo "$1" >> "$GITHUB_STEP_SUMMARY"
    fi
}

file_to_workflow() {
    # Read file content into an array
    mapfile -t file_content < "$1"

    # Print each line from the array
    for line in "${file_content[@]}"; do
        echo "$line" >> "$GITHUB_STEP_SUMMARY"
    done
}

arch="$(dpkg --print-architecture)"
mount_destination_path="/var/snap/dotnet/common/dotnet"
# We take the snap name as an input parameter
for snap in "$@"; do
    content_snap_path="/snap/$snap/current"
    dotnet_path="${content_snap_path}/usr/lib/dotnet"

    print_to_workflow "# $snap-$arch"

    echo "Installing .mount units..."
    cp "$content_snap_path"/mounts/* /usr/lib/systemd/system
    systemctl daemon-reload

    systemctl_status_output_file=$(mktemp)
    for unit_path in "$content_snap_path"/mounts/*.mount; do
        failed="no"
        # Remove the preceding path from the unit name
        unit="$(basename "$unit_path")"

        print_to_workflow "## $unit"

        echo "Starting $unit..."
        print_to_workflow "- Starting unit \`${unit}\` :up:"

        # Start the service without exiting immediately if it fails
        set +e  # Disable 'set -e' temporarily
        systemctl start "$unit"
        start_status=$?  # Capture the exit status of systemctl start
        set -e  # Re-enable 'set -e' for the rest of the script

        # Check if the service failed to start
        if [[ $start_status -ne 0 ]]; then
            print_to_workflow "- Failed to start the unit \`$unit\` :x:"
            print_to_workflow "### Service Log (Last 50 lines)"
            journalctl -u "$unit" -n 50 | tee "$systemctl_status_output_file" | cat
            print_to_workflow "\`\`\`"
            file_to_workflow "$systemctl_status_output_file"
            print_to_workflow "\`\`\`"
            exit 1
        else
            print_to_workflow "- Unit \`${unit}\` started! :ok:"
        fi

        print_to_workflow "### Service Status"
        systemctl status "$unit" | tee "$systemctl_status_output_file" | cat
        print_to_workflow "\`\`\`"
        file_to_workflow "$systemctl_status_output_file"
        print_to_workflow "\`\`\`"

        echo "Checking if mount exists..."
        # We are deriving the path from the unit name because the name
        # is the path itself escaped according to systemd-escape(1).
        escaped_path="/$(basename --suffix=.mount "$unit")"
        unescaped_path="$(systemd-escape --unescape "$escaped_path")"

        if [[ -d "$unescaped_path" ]]; then
            echo "Directory $unescaped_path exists"
            print_to_workflow "- Directory \`$unescaped_path\` exists :white_check_mark:"
        else
            print_to_workflow "- Directory \`$unescaped_path\` does not exist :x:"
            failed="yes"
        fi
        if [[ $(find "$unescaped_path" -maxdepth 1 | wc --lines) -gt 1 ]]; then
            echo "Directory $unescaped_path is not empty"
            print_to_workflow "- Directory \`$unescaped_path\` is not empty :white_check_mark:"
        else
            print_to_workflow "- Directory \`$unescaped_path\` is not empty :x:"
            failed="yes"
        fi

        print_to_workflow "" # Empty line
        if [ $failed = "no" ]; then
            print_to_workflow "**PASS** :white_check_mark:"
        else
            print_to_workflow "**FAIL** :x:"
            exit 1
        fi
    done
done

# Test .NET output
find "$dotnet_path" -maxdepth 1 -type f -exec cp {} "$mount_destination_path" \;
find "$dotnet_path" -maxdepth 1 -type d -name host -exec cp --recursive --dereference \
    --preserve=mode,ownership,timestamps {} "$mount_destination_path" \;

print_to_workflow "## \`dotnet --info\`"

dotnet_info_tmp_file="$(mktemp)"
"$mount_destination_path"/dotnet --info | tee "$dotnet_info_tmp_file" | cat

print_to_workflow "\`\`\`"
file_to_workflow "$dotnet_info_tmp_file"
print_to_workflow "\`\`\`"
