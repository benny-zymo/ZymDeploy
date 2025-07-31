#!/usr/bin/env python3
"""
Log File Serial Data Cleaner
Removes serial input/output debug lines from log files
"""

import os
import sys
from pathlib import Path


def clean_log_file(input_file, output_file=None):
    """
    Clean log file by removing serial input/output lines

    Args:
        input_file (str): Path to the input log file
        output_file (str): Path to the output file (optional)

    Returns:
        str: Path to the cleaned output file
    """
    input_path = Path(input_file)

    # Generate output filename if not provided
    if output_file is None:
        output_file = input_path.stem + "_cleaned" + input_path.suffix

    output_path = Path(output_file)

    # Check if input file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file '{input_file}' not found")

    lines_removed = 0
    lines_kept = 0

    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as infile:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                for line in infile:
                    # Check if line contains serial input/output patterns
                    if ('[SERIAL][IN]' in line or
                            '[SERIAL][OUT]' in line or
                            'Port COM' in line):
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

    return str(output_path)


def main():
    """Main function to handle command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python log_cleaner.py <input_file> [output_file]")
        print("Example: python log_cleaner.py this.log")
        print("Example: python log_cleaner.py this.log cleaned_log.log")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        clean_log_file(input_file, output_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # If run directly, use command line arguments
    if len(sys.argv) > 1:
        main()
    else:
        # Example usage for testing
        try:
            # Clean the log file (assumes 'this.log' exists in current directory)
            clean_log_file('C:/Users/PCP-Zymoptiq/Desktop/routine deploiement/log/ZymoCubeCtrl_DRIFT_FIX.log', 'C:/Users/PCP-Zymoptiq/Desktop/routine deploiement/log/ZymoCubeCtrl_clearn.log')
        except FileNotFoundError:
            print("To use this script:")
            print("1. Save it as 'log_cleaner.py'")
            print("2. Run: python log_cleaner.py this.log")
            print("   or: python log_cleaner.py this.log cleaned_output.log")