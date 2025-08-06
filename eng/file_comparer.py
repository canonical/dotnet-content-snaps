"""
eng/file_comparer.py

This script compares files in multiple origin directories against a destination directory.
It checks for files that are present in the origin directories but missing in the destination,
and also identifies any extra files that exist in the destination but not in the origin directories.
It outputs the differences to standard error and exits with a non-zero status if discrepancies
are found.
"""

import os
import sys

def get_relative_file_list(directory):
    """Get a sorted list of all files in a directory with paths relative to the directory."""
    file_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), directory)
            file_list.append(relative_path)
    return sorted(file_list)

def compare_directories(origins, destination):
    """
    Compare files in origin directories with a destination directory.

    Args:
        origins (list of str): List of origin directories.
        destination (str): Destination directory.
    """
    # Collect unique files from origin directories
    origin_files = set()
    for origin in origins:
        if not os.path.isdir(origin):
            sys.stderr.write(f"Error: Origin directory '{origin}' does not exist.\n")
            sys.exit(1)
        origin_files.update(get_relative_file_list(origin))

    # Collect files from the destination directory
    if not os.path.isdir(destination):
        sys.stderr.write(f"Error: Destination directory '{destination}' does not exist.\n")
        sys.exit(1)
    destination_files = set(get_relative_file_list(destination))

    # Find differences
    missing_in_destination = origin_files - destination_files
    extra_in_destination = destination_files - origin_files

    # Output results
    if missing_in_destination or extra_in_destination:
        sys.stderr.write("Files missing from destination:\n")
        for file in sorted(missing_in_destination):
            sys.stderr.write(f"{file}\n")

        sys.stderr.write("\nExtra files in destination:\n")
        for file in sorted(extra_in_destination):
            sys.stderr.write(f"{file}\n")

        sys.exit(1)
    else:
        print("No differences found. Directories are in sync.")
        sys.exit(0)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare files between origin directories and a destination directory.")
    parser.add_argument("origins", nargs="+", help="List of origin directories.")
    parser.add_argument("destination", help="Destination directory.")

    args = parser.parse_args()

    compare_directories(args.origins, args.destination)
