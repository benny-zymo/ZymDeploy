#!/usr/bin/env python3
"""
Log File Serial Data Cleaner
Removes serial input/output debug lines from log files
Option to keep only the last acquisition
"""

import os
import sys
from pathlib import Path


def clean_log_file(input_file, output_file=None, keep_last_acquisition_only=False):
    """
    Clean log file by removing serial input/output lines
    Optionally keep only the last acquisition

    Args:
        input_file (str): Path to the input log file
        output_file (str): Path to the output file (optional)
        keep_last_acquisition_only (bool): If True, keep only the last acquisition

    Returns:
        str: Path to the cleaned output file
    """
    input_path = Path(input_file)

    # Generate output filename if not provided
    if output_file is None:
        suffix = "_cleaned_last" if keep_last_acquisition_only else "_cleaned"
        output_file = input_path.stem + suffix + input_path.suffix

    output_path = Path(output_file)

    # Check if input file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file '{input_file}' not found")

    lines_removed = 0
    lines_kept = 0
    acquisitions_found = 0

    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as infile:
            all_lines = infile.readlines()

        # If we need to keep only the last acquisition, find it first
        last_acquisition_start = 0
        if keep_last_acquisition_only:
            acquisition_starts = []
            for i, line in enumerate(all_lines):
                if "Starting acquisition" in line:
                    acquisition_starts.append(i)
                    acquisitions_found += 1

            if acquisition_starts:
                last_acquisition_start = acquisition_starts[-1]
                print(
                    f"Found {acquisitions_found} acquisition(s), keeping only the last one starting at line {last_acquisition_start + 1}")
            else:
                print("Warning: No 'Starting acquisition' found in the log file")
                last_acquisition_start = 0

        # Process lines
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for i, line in enumerate(all_lines):
                # Skip lines before last acquisition if option is enabled
                if keep_last_acquisition_only and i < last_acquisition_start:
                    lines_removed += 1
                    continue

                # Check if line contains serial input/output patterns
                if ('[SERIAL][IN]' in line or
                        '[SERIAL][OUT]' in line or
                        'Port COM' in line or
                        'MOTOR' in line or
                        'STEP' in line or
                        'TO POINT' in line or
                        'Seeking' in line or
                        'Stepping' in line):
                    lines_removed += 1
                else:
                    outfile.write(line)
                    lines_kept += 1

    except Exception as e:
        raise Exception(f"Error processing file: {e}")

    print(f"✓ Log file cleaned successfully!")
    print(f"  Input file: {input_path}")
    print(f"  Output file: {output_path}")
    print(f"  Lines kept: {lines_kept}")
    print(f"  Lines removed: {lines_removed}")
    if keep_last_acquisition_only:
        print(f"  Acquisitions found: {acquisitions_found}")
        print(f"  Kept only the last acquisition")

    return str(output_path)


def main():
    """Main function to handle command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python log_cleaner.py <input_file> [output_file] [--last-only]")
        print("Examples:")
        print("  python log_cleaner.py this.log")
        print("  python log_cleaner.py this.log cleaned_log.log")
        print("  python log_cleaner.py this.log --last-only")
        print("  python log_cleaner.py this.log cleaned_log.log --last-only")
        print("")
        print("Options:")
        print("  --last-only    Keep only the last acquisition in the log file")
        sys.exit(1)

    input_file = sys.argv[1]

    # Parse arguments
    keep_last_only = '--last-only' in sys.argv

    # Remove --last-only from args to find output file
    args_without_flag = [arg for arg in sys.argv[1:] if arg != '--last-only']
    output_file = args_without_flag[1] if len(args_without_flag) > 1 else None

    try:
        clean_log_file(input_file, output_file, keep_last_acquisition_only=keep_last_only)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def clean_and_keep_last_acquisition(input_file, output_file=None):
    """
    Convenience function to clean log and keep only last acquisition

    Args:
        input_file (str): Path to the input log file
        output_file (str): Path to the output file (optional)

    Returns:
        str: Path to the cleaned output file
    """
    return clean_log_file(input_file, output_file, keep_last_acquisition_only=True)


if __name__ == "__main__":
    # If run directly, use command line arguments
    if len(sys.argv) > 1:
        main()
    else:
        # Example usage for testing
        try:
            # Clean the log file and keep only last acquisition
            clean_and_keep_last_acquisition(
                'C:/Users/PCP-Zymoptiq/Desktop/routine deploiement/log/nouveau_log/ZymoCubeCtrl.log',
                'C:/Users/PCP-Zymoptiq/Desktop/routine deploiement/log/nouveau_log/ZymoCubeCtrl_cleaned_last.log'
            )
        except FileNotFoundError:
            print("To use this script:")
            print("1. Save it as 'log_cleaner.py'")
            print("2. Run: python log_cleaner.py this.log")
            print("   or: python log_cleaner.py this.log --last-only")
            print("   or: python log_cleaner.py this.log cleaned_output.log --last-only")