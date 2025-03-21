import re
import os
import json

# Terms to ignore
IGNORE_TERMS = [
    r"\[Remastered Version\]",
    r"\[Remastered\]",
    r"\[2011 - Remaster\]",
    r"\(2009 Remaster\)",
    r"\(Remaster 2019\)",
    r"\(Bonus Version\)",
    r"\(Full Moon Edition\)",
    r"\(Deluxe Edition Remastered\)",
    r"\(Deluxe Remastered Edition\)",
    r"\(Special Super Deluxe Box\)",
    r"\(2011 Remastered Version\)",
    r"\(Deluxe Edition\)",
    r"\(2015 stereo mix\)",
    r"\(Deluxe Version\)",
    r"\(Deluxe Album\)",
    r"\(Deluxe\)",
    r"\(Super Deluxe Edition\)",
    r"\(20th Anniversary Remaster\)",
    r"\(30th Anniversary / Deluxe Edition\)",
    r"\(40th Anniversary Deluxe Edition\)",
    r"\(Remastered 1996\)",
    r"\(Prospekt's March Edition\)",
    r"\(Expanded Edition\)",
    r"\(Remastered\)",
    r"- Remastered",
    r"- Live @ San Siro 2015",
    r"- Live",
    r"- edit vrs",
    r"- 2011 Remastered Version",
    r"- Remastered 2020 in 192 KHz",
    r"- Remastered 1996",
    r"- Remastered 2019",
    r"- Remastered 2006",
    r"- 20th Anniversary Remaster",
    r"- Mono / Remastered",
    r"- EP",
    r"EP",
    r"E.P.",
    r": Deluxe Edition",
    r"or Death and All His Friends",
    r"\(Prospekt's March Edition\)",
    r"\(Live\)"
]


def clean_string(input_string):
    """Remove terms to ignore, extra spaces and convert in lowercase."""

    # Sostituzione di caratteri specifici
    input_string = input_string.replace("’", "'")
    input_string = input_string.replace("×", "x")
    input_string = input_string.replace("·", "")
    input_string = input_string.replace("‐", "-")
    input_string = input_string.replace("…", "...")
    input_string = input_string.replace(" / ", "/")
    input_string = input_string.replace("E'", "è")
    input_string = input_string.replace("Sansiro", "San siro")
    input_string = input_string.replace(" - ", "-")
    input_string = input_string.replace("I RIO", "Rio")
    
    input_string = input_string.strip().lower()
    
    for term in IGNORE_TERMS:
        input_string = re.sub(term, "", input_string, flags=re.IGNORECASE)
    return input_string.strip()

def album_title_match(input_string):
    """Manual match for irregoular album title."""
    input_string = input_string.replace("Greatest Hits Volume One - The Singles", "Greatest Hits, Volume One: The Singles")
    return input_string

##############################
### READ FILE UTILS
##############################

def load_json_data(file_path):
    """Load data from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_set_from_file(file_path):
    """Load a set from a file's rows."""
    with open(file_path, "r", encoding="utf-8") as f:
        return set(f.read().splitlines())

##############################
### WRITE FILE UTILS
##############################

def sanitize_filename(name):
    """Clean a filename from not allowed char. (for Windows)"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def append_dir_to_file_name(filename, output_dir=None):
    """Append dir to file name and eventually create directory if not exist."""
    if output_dir:  # None/empty string check
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"{filename}")
    return filename

def save_to_json_file(data, filename, output_dir=None, append=False):
    """Save data in a JSON file. Append to existing data if 'append' is True."""
    filename = append_dir_to_file_name(sanitize_filename(filename), output_dir)

    # If append is set to true, load existing JSON file
    if append and os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            try:
                existing_data = json.load(file)
                # Check if data are of the same type
                if isinstance(existing_data, list) and isinstance(data, list):
                    data = existing_data + data
                elif isinstance(existing_data, dict) and isinstance(data, dict):
                    existing_data.update(data)
                    data = existing_data
                else:
                    raise ValueError("Cannot append: Data types do not match.")
            except json.JSONDecodeError:
                print(f"Warning: Existing file {filename} contains invalid JSON. Overwriting.")
    
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    print(f"Data saved in the file '{filename}'.")

def save_row_to_text_file(row, filename, output_dir=None):
    """Save row in a text file."""
    filename = sanitize_filename(append_dir_to_file_name(filename, output_dir))

    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{row}\n")

    print(f"Data saved in the file '{filename}'.")