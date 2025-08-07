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
import fnmatch


def read_ignore_file(ignore_file):
    """Read the ignore file and return a set of patterns to ignore."""
    if not ignore_file:
        return set()
    try:
        with open(ignore_file, 'r', encoding='utf-8') as f:
            return {line.strip() for line in f if line.strip() and not line.startswith('#')}
    except IOError as e:
        sys.stderr.write(f"Error reading ignore file: {e}\n")
        sys.exit(1)


def get_relative_file_list(directory, ignore_patterns=None):
    """
    Get a sorted list of all files in a directory with paths relative to the directory.

    Args:
        directory (str): The directory to scan.
        ignore_patterns (set): Set of glob patterns to ignore. Supports * wildcards.
    """
    file_list = []
    ignore_patterns = ignore_patterns or set()

    for root, _, files in os.walk(directory):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), directory)
            # Use fnmatch to support glob patterns like *.nupkg
            if not any(fnmatch.fnmatch(relative_path, pattern) for pattern in ignore_patterns):
                file_list.append(relative_path)
    return sorted(file_list)


def compare_directories(origins, destination, ignore_file=None):
    """
    Compare files in origin directories with a destination directory.

    Args:
        origins (list of str): List of origin directories.
        destination (str): Destination directory.
        ignore_file (str, optional): Path to file containing patterns to ignore.
    """
    # Read ignore patterns
    ignore_patterns = read_ignore_file(ignore_file)

    # Collect unique files from origin directories
    origin_files = set()
    for origin in origins:
        if not os.path.isdir(origin):
            sys.stderr.write(f"Error: Origin directory '{origin}' does not exist.\n")
            sys.exit(1)
        origin_files.update(get_relative_file_list(origin, ignore_patterns))

    # Collect files from the destination directory
    if not os.path.isdir(destination):
        sys.stderr.write(f"Error: Destination directory '{destination}' does not exist.\n")
        sys.exit(1)
    destination_files = set(get_relative_file_list(destination, ignore_patterns))

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
    parser.add_argument("--ignore-file", "-i",
                        help="File containing patterns to ignore (one per line).")

    args = parser.parse_args()

    compare_directories(args.origins, args.destination, args.ignore_file)
