import os
from pathlib import Path

def concatenate_bitcoin_files(directory_path, output_filename="combined_bitcoin_reports.html"):
    # Get the directory path
    reports_dir = Path(directory_path)
    
    # Initialize HTML content with Pico CSS and proper structure
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bitcoin Research Reports</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <style>
        /* Custom styles */
        .container {
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        .report-meta {
            color: var(--muted-color);
            font-size: 0.9rem;
        }
        article {
            margin-bottom: 2rem;
            padding: 2rem;
            border-radius: 8px;
            background: var(--card-background-color);
        }
        nav {
            position: sticky;
            top: 0;
            background: var(--background-color);
            padding: 1rem 0;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <nav class="container">
        <ul>
            <li><strong>Bitcoin Research Reports</strong></li>
        </ul>
    </nav>
    <main class="container">
"""
    
    # Find all markdown files containing 'bitcoin' (case insensitive)
    bitcoin_files = [f for f in reports_dir.glob("*.md") 
                    if 'bitcoin' in f.name.lower()]
    
    # Sort files alphabetically for consistent output
    bitcoin_files.sort()
    
    # Add table of contents
    html_content += '<div role="document">\n<h2>Table of Contents</h2>\n<ul>\n'
    for file_path in bitcoin_files:
        file_id = file_path.stem.lower().replace(' ', '-')
        html_content += f'<li><a href="#{file_id}">{file_path.stem}</a></li>\n'
    html_content += '</ul></div>\n\n'
    
    # Process each file
    for file_path in bitcoin_files:
        try:
            file_id = file_path.stem.lower().replace(' ', '-')
            
            # Create article section for each report
            html_content += f'<article id="{file_id}">\n'
            html_content += f'<h2>{file_path.stem}</h2>\n'
            
            # Read and append content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Convert markdown content to basic HTML
                # This is a simple conversion - you might want to use a proper markdown parser
                paragraphs = content.split('\n\n')
                for p in paragraphs:
                    if p.strip():
                        html_content += f'<p>{p}</p>\n'
            
            html_content += f'<div class="report-meta">Source: {file_path.name}</div>\n'
            html_content += '</article>\n\n'
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    # Close HTML structure
    html_content += """
    </main>
    <footer class="container">
        <small>Generated from {len(bitcoin_files)} Bitcoin research reports</small>
    </footer>
</body>
</html>
"""
    
    # Write combined content to new file
    output_path = reports_dir / output_filename
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Successfully created {output_filename}")
        print(f"Combined {len(bitcoin_files)} Bitcoin-related files")
    except Exception as e:
        print(f"Error writing output file: {str(e)}")

if __name__ == "__main__":
    # Get the current script's directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    concatenate_bitcoin_files(current_dir)