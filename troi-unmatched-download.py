#!/usr/bin/env python3
"""
Script to convert unmatched album data to Qobuz search commands.
Takes a file with album/artist lines and generates search commands in the format:
/search qobuz album [ALBUM] [ARTISTA]
"""

import sys
import argparse
from pathlib import Path
import troi_utils


def process_unmatched_file(input_file, output_file=None):
    """
    Process the unmatched file and generate search commands.
    
    Args:
        input_file (str): Path to input file
        output_file (str): Path to output file (optional)
    """
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: Input file '{input_file}' not found")
        return False
    
    # Determine output file name
    if output_file is None:
        output_file = input_path.stem + "_commands.txt"
    
    try:
        # Use troi_utils to parse the file
        albums = troi_utils.get_unique_albums(input_file)
        commands = troi_utils.format_search_commands(albums, "qobuz")
    
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    # Write commands to output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for command in commands:
                f.write(command + '\n')
        
        print(f"Generated {len(commands)} search commands")
        print(f"Output written to: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert unmatched album data to Qobuz search commands"
    )
    parser.add_argument(
        "input_file",
        help="Input file containing unmatched albums"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file for search commands (default: input_file_commands.txt)"
    )
    
    args = parser.parse_args()
    
    success = process_unmatched_file(args.input_file, args.output)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())