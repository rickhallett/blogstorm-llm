from gpt_researcher import GPTResearcher
import asyncio
import sys
import argparse
from openai import AsyncOpenAI
import os
import json

async def get_report(query: str, report_type: str) -> str:
    researcher = GPTResearcher(query, report_type)
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()

    research_context = researcher.get_research_context()
    research_costs = researcher.get_costs()
    research_sources = researcher.get_research_sources()
    research_subtopics = await researcher.get_subtopics()

    return research_result, report, research_context, research_costs, research_sources, research_subtopics

async def generate_title(report: str) -> str:
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Generate a concise, descriptive title for this research report. Use only alphanumeric characters, spaces, and underscores. Keep it under 60 characters."},
            {"role": "user", "content": report}
        ]
    )
    return response.choices[0].message.content.strip()

async def write_report(query: str, report_type: str, recursions: int = 0):
    result, report, context, costs, sources, subtopics = await get_report(query, report_type)
    
    # Convert Subtopics object to list of task strings
    subtopic_list = [subtopic.task for subtopic in subtopics.subtopics]
    
    # Generate title from report content
    title = await generate_title(report)
    safe_title = title.replace(' ', '_').replace('-', '_')
    file_path = f"./src/researcher/reports/{safe_title}.md"

    # Create the reports directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    report_content = f"""
            Report:
            {report}
            Research Costs:
            {costs}
            Research Sources:
            {json.dumps(sources, indent=4)}
            Research Subtopics:
            {subtopic_list}
            """

    try:
        with open(file_path, "w") as f:
            f.write(report_content)
    except Exception as e:
        print(f"Error writing report: {e}")

        with open(f"./{safe_title}.md", "w") as f:
            f.write(report_content)

    for subtopic in subtopic_list:
        new_query = f"{query}: Deep dive into {subtopic}"
        recursions += 1
        if recursions < 3:
            await write_report(new_query, report_type, recursions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a research report.")
    parser.add_argument('--query', type=str, required=True, help='The query for the research report')
    args = parser.parse_args()

    query = args.query
    report_type = "research_report"
    
    asyncio.run(write_report(query, report_type))



