// Sample test data for various scenarios

export const sampleIdea = {
  idea: "Writing effective technical documentation",
  targetLength: "medium",
  tone: "professional"
};

export const sampleOutline = {
  title: "Writing Effective Technical Documentation",
  mainThesis: "Good technical documentation is crucial for project success",
  keyPoints: [
    "Clear structure is essential",
    "Examples help understanding",
    "Regular updates maintain relevance"
  ],
  sections: [
    {
      heading: "Introduction",
      points: ["Importance of documentation", "Common challenges"]
    },
    {
      heading: "Best Practices",
      points: ["Use clear language", "Include examples", "Regular updates"]
    }
  ]
};

export const sampleMarkdownContent = `
# Writing Effective Technical Documentation

Good technical documentation is crucial for project success.

## Introduction
Importance of documentation cannot be overstated...

## Best Practices
Use clear language and include examples...
`;

export const sampleEnhanceRequest = {
  content: sampleMarkdownContent,
  focusAreas: ["clarity", "engagement"]
};

export const sampleGhostContent = {
  content: sampleMarkdownContent,
  metadata: {
    title: "Writing Effective Technical Documentation",
    slug: "writing-effective-technical-documentation",
    tags: ["technical-writing", "documentation"]
  }
};
