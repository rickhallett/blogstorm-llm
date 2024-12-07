# BlogStorm LLM

This service handles content transformation for BlogStorm. Each endpoint operates independently, performing specific content enhancement tasks. The service is designed around the principle of single responsibility, where each endpoint focuses on one aspect of content transformation.

## Overview

The LLM Service takes various forms of input content and enhances it through different stages of AI processing. Each endpoint represents a distinct transformation stage and can be used independently or as part of a larger content pipeline. [BlogStorm Publish](https://github.com/rickhallett/blogstorm-publish) uses this service to transform content for publication.

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- OpenAI API key
- PostgreSQL database

### Installation

1. Clone the repository
2. Install dependencies: `npm install`
3. Copy `.env.example` to `.env` and fill in required values
4. Run migrations: `npx prisma migrate dev`
5. Start the server: `npm run dev`

## API Documentation

### POST /api/transform/expand-idea

Transforms initial brainstorming into a structured article outline.

Request Body:

```json
{
  "idea": "string", // Initial brainstorming text
  "targetLength": "short | medium | long", // Optional, defaults to medium
  "tone": "casual | professional" // Optional, defaults to casual
}
```

Response:

```json
{
  "outline": {
    "title": "string",
    "mainThesis": "string",
    "keyPoints": ["string"],
    "sections": [
      {
        "heading": "string",
        "points": ["string"]
      }
    ]
  },
  "metadata": {
    "suggestedTags": ["string"],
    "estimatedReadTime": "number"
  }
}
```

### POST /api/transform/generate-draft

Creates a full article draft from a structured outline.

Request Body:

```json
{
  "outline": {
    "title": "string",
    "mainThesis": "string",
    "keyPoints": ["string"],
    "sections": [
      {
        "heading": "string",
        "points": ["string"]
      }
    ]
  }
}
```

Response:

```json
{
  "content": "string", // Markdown formatted article
  "metadata": {
    "wordCount": "number",
    "readingTime": "number",
    "headings": ["string"]
  }
}
```

### POST /api/transform/enhance

Improves the quality and engagement of an existing draft.

Request Body:

```json
{
  "content": "string", // Markdown formatted article
  "focusAreas": ["clarity", "engagement", "tone"]
}
```

Response:

```json
{
  "enhancedContent": "string",
  "changes": [
    {
      "type": "string",
      "description": "string"
    }
  ]
}
```

### POST /api/transform/prepare-ghost

Prepares content for publishing to Ghost, including metadata generation.

Request Body:

```json
{
  "content": "string" // Markdown formatted article
}
```

Response:

```json
{
  "title": "string",
  "slug": "string",
  "metaDescription": "string",
  "tags": ["string"],
  "content": "string", // Ghost-formatted content
  "excerpt": "string"
}
```

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {} // Optional additional information
  }
}
```

Common error codes:

- `INVALID_INPUT`: Request body fails validation
- `LLM_ERROR`: Error communicating with OpenAI
- `PROCESSING_ERROR`: Error during content transformation
- `RATE_LIMIT`: Too many requests to LLM service

## Development

### Testing

Run tests with: `npm test`

Test coverage report: `npm run test:coverage`

### Environment Variables

```
PORT=3001
DATABASE_URL=postgresql://user:password@localhost:5432/llm_pipeline
OPENAI_API_KEY=your_api_key
NODE_ENV=development
```

## Monitoring and Logging

The service includes detailed logging of:

- Processing duration for each transformation
- LLM token usage
- Error rates and types
- Request patterns

Access logs are available at `/logs` in development mode.

## Architecture Notes

Each endpoint is designed to function independently, following the single responsibility principle. This allows for:

- Independent scaling of different transformation types
- Isolated testing and monitoring
- Flexible pipeline composition
- Easier maintenance and updates

The service uses a queue system for long-running transformations, with results stored in the database for reliability.
