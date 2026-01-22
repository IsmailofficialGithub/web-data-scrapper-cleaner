"""
HTML Data Cleaner
Takes an HTML file, extracts text from all nodes, and saves cleaned text to a txt file.
"""

from bs4 import BeautifulSoup
import re
import sys
import os
from datetime import datetime


def clean_html_data(input_file, output_file=None):
    """
    Clean HTML file and extract text content from all nodes.
    
    Args:
        input_file (str): Path to the HTML file to clean
        output_file (str, optional): Output file path. If None, generates automatically.
    
    Returns:
        str: Path to the output file, or None if error
    """
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found!")
        return None
    
    print(f"Reading HTML file: {input_file}")
    
    try:
        # Read HTML file
        with open(input_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse HTML with BeautifulSoup
        print("Parsing HTML content...")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        print("Removing scripts, styles, and metadata...")
        for element in soup(["script", "style", "meta", "link", "noscript", "head"]):
            element.decompose()
        
        # Get text from all nodes
        print("Extracting text from nodes...")
        text_content = soup.get_text()
        
        # Clean the text
        print("Cleaning text content...")
        # Split into lines
        lines = text_content.split('\n')
        # Remove empty lines and strip whitespace
        cleaned_lines = []
        for line in lines:
            cleaned_line = line.strip()
            # Remove lines that are too short or only whitespace
            if cleaned_line and len(cleaned_line) > 1:
                cleaned_lines.append(cleaned_line)
        
        # Join lines with newlines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove excessive blank lines (more than 2 consecutive newlines)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        # Generate output filename if not provided
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{base_name}_cleaned_{timestamp}.txt"
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else '.'
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save cleaned text to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        print(f"✓ Cleaned text saved to: {output_file}")
        print(f"✓ Original size: {len(html_content)} characters")
        print(f"✓ Cleaned size: {len(cleaned_text)} characters")
        print(f"✓ Lines extracted: {len(cleaned_lines)}")
        
        return output_file
        
    except Exception as e:
        print(f"Error cleaning HTML file: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function to handle command line arguments or interactive mode"""
    if len(sys.argv) < 2:
        # Interactive mode
        print("=" * 50)
        print("HTML Data Cleaner - Interactive Mode")
        print("=" * 50)
        print()
        
        input_file = input("Enter HTML file path: ").strip()
        if not input_file:
            print("Error: File path cannot be empty!")
            sys.exit(1)
        
        output_file = input("Enter output filename (press Enter for auto-generated): ").strip()
        if not output_file:
            output_file = None
        
        print()
        clean_html_data(input_file, output_file)
    else:
        # Command line mode
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        clean_html_data(input_file, output_file)


if __name__ == "__main__":
    main()
