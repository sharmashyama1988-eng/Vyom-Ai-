"""
This file was corrupted and has been restored with a simplified version.
The original file likely contained functions to read various file types like pdf, docx, etc.
This simplified version only handles text files.
"""
import os

def read_any_file(file_path):
    """
    Reads the content of a file.
    This is a simplified version and only handles text files.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

if __name__ == '__main__':
    # This file is not meant to be run directly.
    # It is a module that provides the read_any_file function.
    print("This is a module and is not meant to be run directly.")
