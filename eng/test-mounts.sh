#!/usr/bin/env bash
set -xeuo pipefail
IFS=$'\n\t'

# We take the snap name as an input parameter
snap="$1"
dotnet_path="$2"
content_snap_path="/snap/$snap/current"

# Test .NET output
"$dotnet_path"/dotnet --info

echo "Installing .mount units..."
cp "$content_snap_path"/mounts/* /usr/lib/systemd/system
systemctl daemon-reload

for unit_path in "$content_snap_path"/mounts/*.mount; do
    # Remove the preceding path from the unit name
    unit=$(basename "$unit_path")

    echo "Starting $unit..."
    systemctl start "$unit"
    systemctl status "$unit"

    echo "Checking if mount exists..."
    # We are deriving the path from the unit name because the name
    # is the path itself escaped according to systemd-escape(1).
    escaped_path="/$(basename --suffix=.mount "$unit")"
    unescaped_path=$(systemd-escape --unescape "$escaped_path")

    [[ -d $unescaped_path ]] && echo "Directory $unescaped_path exists"
    [[ $(find "$unescaped_path" -maxdepth 1 | wc --lines) -gt 1 ]] && echo "Directory $unescaped_path is not empty"
done
