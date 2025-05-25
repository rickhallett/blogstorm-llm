#!/usr/bin/env python3
import asyncio
import argparse
import os
import re
import html
import json
import signal
import pickle
from pathlib import Path
from gpt_researcher import GPTResearcher
import hashlib
import datetime
from openai import AsyncOpenAI

# ------------------------------------------------------------------------------
# This script demonstrates how to:
#  1) Take an initial query from the command line
#  2) Generate an HTML output file that concatenates the various sections
#  3) Recursively call subtopics up to a maximum depth of 3
#  4) Build a tree of contents at the start with links into the content
# ------------------------------------------------------------------------------

MAX_DEPTH = 2

class ResearchStats:
    def __init__(self):
        self.total_queries = 0
        self.total_cost = 0.0

class GracefulExit(Exception):
    pass

def slugify(text: str, max_length: int = 100) -> str:
    """
    Create a URL-friendly anchor from a string, with length limitation.
    For cache files, adds a hash to maintain uniqueness when truncated.
    """
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip()).strip("-").lower()
    
    if len(slug) <= max_length:
        return slug
    
    # For long slugs, truncate and add hash to maintain uniqueness
    hash_suffix = hashlib.md5(text.encode()).hexdigest()[:8]
    truncated_length = max_length - len(hash_suffix) - 1
    return f"{slug[:truncated_length]}-{hash_suffix}"

def signal_handler(signum, frame):
    raise GracefulExit()

async def get_report_data(query: str, depth: int = 0, stats: ResearchStats = None, cache_dir: Path = None):
    """
    Recursively obtain a research report and subtopics (up to MAX_DEPTH).
    Return a nested dictionary structure with the data and any children.
    """
    if stats is None:
        stats = ResearchStats()
    
    # Add depth check early to prevent recursion issues
    if depth >= MAX_DEPTH:
        return None
    
    # Create cache filename from query with length limit
    cache_file = None
    if cache_dir:
        cache_filename = slugify(query, max_length=100) + ".pickle"  # Limit filename length
        cache_file = cache_dir / cache_filename
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except (EOFError, pickle.UnpicklingError):
                # If cache file is corrupted, delete it and continue with fresh research
                print(f"Warning: Corrupted cache file found for '{query}'. Regenerating...")
                cache_file.unlink()

    stats.total_queries += 1
    node_data = {
        "query": query,
        "report": "",
        "research_result": [],
        "costs": 0.0,
        "subtopics": []
    }
    
    try:
        # Create a GPTResearcher object
        researcher = GPTResearcher(query, "research_report")

        # Using the library to conduct the research
        research_result = await researcher.conduct_research()
        report = await researcher.write_report()
        costs = researcher.get_costs()
        stats.total_cost += costs
        subtopics_obj = await researcher.get_subtopics()

        # Update node data
        node_data.update({
            "report": report,
            "research_result": research_result,
            "costs": costs,
        })

        # Cache the current node's data
        if cache_file:
            with open(cache_file, 'wb') as f:
                pickle.dump(node_data, f)

        # If we haven't reached maximum depth, recurse
        if depth < MAX_DEPTH and subtopics_obj and hasattr(subtopics_obj, 'subtopics'):
            for subtopic in subtopics_obj.subtopics:
                new_query = f"{query}: {subtopic.task}"
                child_data = await get_report_data(new_query, depth + 1, stats, cache_dir)
                if child_data:
                    node_data["subtopics"].append(child_data)
            # Update cache with new child data
            if cache_file:
                with open(cache_file, 'wb') as f:
                    pickle.dump(node_data, f)

        return node_data

    except GracefulExit:
        print(f"\nGracefully stopping after completing query: {query}")
        return node_data
    except Exception as e:
        print(f"Error processing query '{query}': {e}")
        return node_data  # Return partial data instead of None

def build_html_toc(data, indent=0):
    """
    Build an HTML <ul> table-of-contents tree for all queries,
    linking to anchored sections further down in the HTML.
    Only shows the main query at each level, with subtopics nested underneath.
    """
    spaces = "    " * indent
    slug = slugify(data["query"].split(": ")[-1])  # Get just the last part after ":"
    display_text = data["query"].split(": ")[-1]    # Display only the subtopic part
    
    toc_html = f'{spaces}<li><a href="#{slug}">{html.escape(display_text)}</a></li>\n'
    if data["subtopics"]:
        toc_html += f"{spaces}<ul>\n"
        for sub in data["subtopics"]:
            toc_html += build_html_toc(sub, indent + 1)
        toc_html += f"{spaces}</ul>\n"
    return toc_html

def build_html_content(data, indent=0):
    """
    Build the detailed HTML content for this query and subtopics.
    """
    slug = slugify(data["query"])
    
    # Create article section for this report
    content_html = f'<article id="{slug}">\n'
    content_html += f'<h2>{html.escape(data["query"])}</h2>\n'
    
    # Add the main report content
    content_html += f'<div class="report-content">{html.escape(data["report"])}</div>\n'
    
    # Add research costs in a meta section
    content_html += f'<div class="report-meta">Research Costs: ${data["costs"]:.2f}</div>\n'
    
    content_html += '</article>\n'

    # Recursively build subtopics
    for sub in data["subtopics"]:
        content_html += build_html_content(sub, indent + 1)

    return content_html

async def get_suggested_filename(query: str, researcher: GPTResearcher) -> str:
    """
    Get a short, descriptive filename suggestion from the LLM for the research topic.
    """
    prompt = """Generate a short (5-20 words), descriptive filename for this research topic. 
    Use only lowercase letters, numbers, and hyphens. Do not include file extensions.
    Topic: {query}
    Filename: """
    
    # Use OpenAI directly instead of researcher's get_response
    client = AsyncOpenAI()
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates filenames."},
            {"role": "user", "content": prompt.format(query=query)}
        ],
        temperature=0.7,
        max_tokens=50
    )
    
    filename = response.choices[0].message.content.strip()
    # Clean the filename and add timestamp
    clean_name = re.sub(r"[^a-z0-9-]", "-", filename.lower().strip())
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{clean_name}-{timestamp}"

async def main():
    parser = argparse.ArgumentParser(description="Generate an HTML Research Report recursively.")
    parser.add_argument("--query", type=str, required=True, help="The initial query for the research report.")
    parser.add_argument("--output", type=str, help="HTML output file name (optional).")
    parser.add_argument("--cache-dir", type=str, default="./research_cache", help="Directory to store intermediate results.")
    args = parser.parse_args()

    # Set up signal handling for graceful interruption
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create cache directory
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(exist_ok=True)

    # Create stats object to track queries
    stats = ResearchStats()

    try:
        # Create initial researcher for filename generation
        initial_researcher = GPTResearcher(args.query, "research_report")
        
        # Generate output filename if not provided
        if not args.output:
            filename = await get_suggested_filename(args.query, initial_researcher)
            output_dir = os.path.dirname(__file__)
            args.output = os.path.join(output_dir, f"{filename}.html")

        # Get the nested data from GPTResearcher
        report_data = await get_report_data(args.query, depth=0, stats=stats, cache_dir=cache_dir)
        
        if report_data:
            # Build Table of Contents
            toc_html = '<div role="document">\n<h2>Table of Contents</h2>\n<ul>\n'
            toc_html += build_html_toc(report_data)
            toc_html += '</ul>\n</div>'

            # Build the main body content
            body_html = build_html_content(report_data)

            # Wrap everything in a full HTML page with Pico CSS
            final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPT Researcher Report</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <style>
        /* Custom styles */
        .container {{
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .report-meta {{
            color: var(--muted-color);
            font-size: 0.9rem;
            margin-top: 1rem;
        }}
        .report-content {{
            white-space: pre-wrap;
            font-family: var(--font-family);
            line-height: 1.6;
        }}
        article {{
            margin-bottom: 2rem;
            padding: 2rem;
            border-radius: 8px;
            background: var(--card-background-color);
        }}
        nav {{
            position: sticky;
            top: 0;
            background: var(--background-color);
            padding: 1rem 0;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            z-index: 100;
        }}
        [role="document"] {{
            margin-bottom: 3rem;
        }}
    </style>
</head>
<body>
    <nav class="container">
        <ul>
            <li><strong>GPT Researcher Report</strong></li>
            <li><small>Query: {html.escape(args.query)}</small></li>
        </ul>
    </nav>
    <main class="container">
        {toc_html}
        {body_html}
    </main>
    <footer class="container">
        <small>Total queries executed: {stats.total_queries}</small><br>
        <small>Total cost: ${stats.total_cost:.2f}</small>
    </footer>
</body>
</html>
"""
            # Write to file
            output_path = args.output
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_html)
            print(f"\nResearch report generated: {output_path}")
            print(f"Total queries executed: {stats.total_queries}")
            print(f"Total cost: ${stats.total_cost:.2f}")

    except GracefulExit:
        print("\nScript interrupted. Partial results have been cached.")
        print(f"To resume, run the script again with the same query and cache directory.")

if __name__ == "__main__":
    asyncio.run(main())