import os
import re

def clean_markdown_files(directory):
    """
    Recursively find all markdown files in the given directory and remove
    'Research Sources:' line and everything after it.
    """
    # Walk through all files in directory and subdirectories
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                
                # Read file content
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find the 'Research Sources:' line and everything before it
                pattern = r'(.*?)Research Sources:.*'
                match = re.match(pattern, content, re.DOTALL)
                
                if match:
                    # Keep only the content before 'Research Sources:'
                    cleaned_content = match.group(1).rstrip()
                    
                    # Write the cleaned content back to the file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                        print(f"Cleaned {filepath}")

if __name__ == "__main__":
    # Assuming the script is run from the project root directory
    reports_dir = "src/researcher/reports"
    clean_markdown_files(reports_dir)