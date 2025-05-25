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

# ------------------------------------------------------------------------------
# This script demonstrates how to:
#  1) Take an initial query from the command line
#  2) Generate an HTML output file that concatenates the various sections
#  3) Recursively call subtopics up to a maximum depth of 3
#  4) Build a tree of contents at the start with links into the content
# ------------------------------------------------------------------------------

MAX_DEPTH = 1

class ResearchStats:
    def __init__(self):
        self.total_queries = 0
        self.total_cost = 0.0

class GracefulExit(Exception):
    pass

def slugify(text: str) -> str:
    """
    Create a URL-friendly anchor from a string.
    """
    return re.sub(r"[^a-zA-Z0-9]+", "-", text.strip()).strip("-").lower()

def signal_handler(signum, frame):
    raise GracefulExit()

async def get_report_data(query: str, depth: int = 0, stats: ResearchStats = None, cache_dir: Path = None):
    """
    Recursively obtain a research report and subtopics (up to MAX_DEPTH).
    Return a nested dictionary structure with the data and any children.
    """
    if stats is None:
        stats = ResearchStats()
    
    # Create cache filename from query
    cache_file = None
    if cache_dir:
        cache_file = cache_dir / f"{slugify(query)}.pickle"
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

    stats.total_queries += 1
    
    try:
        # Create a GPTResearcher object
        researcher = GPTResearcher(query, "research_report")

        # Using the library to conduct the research
        research_result = await researcher.conduct_research()
        report = await researcher.write_report()
        context = researcher.get_research_context()
        costs = researcher.get_costs()
        stats.total_cost += sum(costs.values())
        sources = researcher.get_research_sources()
        subtopics_obj = await researcher.get_subtopics()

        # Prepare the dictionary node for this query
        node_data = {
            "query": query,
            "report": report, 
            "research_result": research_result,
            "context": context,
            "costs": costs,
            "sources": sources,
            "subtopics": []
        }

        # Cache the current node's data
        if cache_file:
            with open(cache_file, 'wb') as f:
                pickle.dump(node_data, f)

        # If we haven't reached maximum depth, recurse
        if depth < MAX_DEPTH:
            for subtopic in subtopics_obj.subtopics:
                new_query = f"{query}: {subtopic.task}"
                child_data = await get_report_data(new_query, depth + 1, stats, cache_dir)
                node_data["subtopics"].append(child_data)
                # Update cache with new child data
                if cache_file:
                    with open(cache_file, 'wb') as f:
                        pickle.dump(node_data, f)

        return node_data

    except GracefulExit:
        print(f"\nGracefully stopping after completing query: {query}")
        return node_data if 'node_data' in locals() else None
    except Exception as e:
        print(f"Error processing query '{query}': {e}")
        return None

def build_html_toc(data, indent=0):
    """
    Build an HTML <ul> table-of-contents tree for all queries,
    linking to anchored sections further down in the HTML.
    """
    spaces = "    " * indent
    slug = slugify(data["query"])
    toc_html = f'{spaces}<li><a href="#{slug}">{html.escape(data["query"])}</a></li>\n'
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
    # Basic heading for this section
    content_html = f'<h2 id="{slug}">{html.escape(data["query"])}</h2>\n'
    
    # The main body of the report
    content_html += "<pre>\n"
    content_html += f"Report:\n{html.escape(data['report'])}\n\n"
    content_html += f"Research Costs:\n{html.escape(str(data['costs']))}\n\n"
    content_html += "Research Sources:\n"
    content_html += f"{html.escape(json.dumps(data['sources'], indent=4))}\n\n"
    content_html += "</pre>\n"

    # Recursively build subtopics
    for sub in data["subtopics"]:
        content_html += build_html_content(sub, indent + 1)

    return content_html

async def main():
    parser = argparse.ArgumentParser(description="Generate an HTML Research Report recursively.")
    parser.add_argument("--query", type=str, required=True, help="The initial query for the research report.")
    parser.add_argument("--output", type=str, default="research_report.html", help="HTML output file name.")
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
        # Get the nested data from GPTResearcher
        report_data = await get_report_data(args.query, depth=0, stats=stats, cache_dir=cache_dir)
        
        if report_data:
            # Build Table of Contents
            toc_html = "<ul>\n" + build_html_toc(report_data) + "</ul>\n"

            # Build the main body content
            body_html = build_html_content(report_data)

            # Wrap everything in a full HTML page
            final_html = f"""\
<html>
<head>
    <meta charset="utf-8"/>
    <title>GPT Researcher Report</title>
</head>
<body>
    <h1>Table of Contents</h1>
    {toc_html}
    <hr/>
    {body_html}
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