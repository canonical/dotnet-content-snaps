"""
file_comparer.py

This script compares files in multiple origin directories against a
destination directory. It checks for files that are present in the origin
directories but missing in the destination, and also identifies any extra
files that exist in the destination but not in the origin directories. It
outputs the differences to standard error and exits with a non-zero status
if discrepancies are found.
"""

import os
import sys
import fnmatch


def read_ignore_file(ignore_file: str):
    """
    Read the ignore file and return a set of patterns to ignore.

    Args:
        ignore_file (str): The ignore file to read.
    """
    ignore_patterns = set()

    if not ignore_file:
        return ignore_patterns

    try:
        with open(ignore_file, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith('#'):
                    continue

                stripped_line = line.strip()
                if stripped_line:
                    ignore_patterns.add(stripped_line)
    except IOError as error:
        sys.stderr.write(f"Error reading ignore file: {error}\n")
        sys.exit(1)

    return ignore_patterns


def get_relative_file_list(directory: str, ignore_patterns: set[str] = None):
    """
    Get a sorted list of all files in a directory with paths relative to the
    directory.

    Args:
        directory (str): The directory to scan.
        ignore_patterns (set of str): Set of glob patterns to ignore.
                                      Supports * wildcards.
    """
    file_list = []
    if ignore_patterns is None:
        ignore_patterns = set()

    for root, _, files in os.walk(directory):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file),
                                            directory)
            # Skip if it matches any ignore glob pattern (like *.nupkg)
            if any(
                    fnmatch.fnmatch(relative_path, pattern)
                    for pattern in ignore_patterns):
                continue

            file_list.append(relative_path)
    return sorted(file_list)


def compare_directories(origins: set[str],
                        destination: str,
                        ignore_file: str = None):
    """
    Compare files in origin directories with a destination directory.

    Args:
        origins (set of str): List of origin directories.
        destination (str): Destination directory.
        ignore_file (str, optional): Path to file containing patterns to
                                     ignore.
    """
    # Read ignore patterns
    ignore_patterns = read_ignore_file(ignore_file)

    # Collect unique files from origin directories
    origin_files = set()
    for origin in origins:
        if not os.path.isdir(origin):
            sys.stderr.write(
                f"Error: Origin directory '{origin}' does not exist.\n")
            sys.exit(1)
        origin_files.update(get_relative_file_list(origin, ignore_patterns))

    # Collect files from the destination directory
    if not os.path.isdir(destination):
        sys.stderr.write(
            f"Error: Destination directory '{destination}' does not exist.\n")
        sys.exit(1)
    destination_files = set(
        get_relative_file_list(destination, ignore_patterns))

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
        description="""
This script compares files in multiple origin directories against a
destination directory. It checks for files that are present in the origin
directories but missing in the destination, and also identifies any extra
files that exist in the destination but not in the origin directories. It
outputs the differences to standard error and exits with a non-zero status
if discrepancies are found.""")
    parser.add_argument("origins",
                        nargs="+",
                        help="List of origin directories.")
    parser.add_argument("destination", help="Destination directory.")
    parser.add_argument(
        "--ignore-file",
        "-i",
        help="File containing patterns to ignore (one per line).")

    args = parser.parse_args()

    compare_directories(args.origins, args.destination, args.ignore_file)
