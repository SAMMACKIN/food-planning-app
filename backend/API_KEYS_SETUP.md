# AI Provider API Keys Setup

The Food Planning App uses AI services for generating meal recommendations and book recommendations. You need to configure at least one AI provider API key for these features to work.

## Quick Start

1. Open the `backend/.env` file
2. Replace the placeholder values with your actual API keys
3. Restart the backend server

## Available AI Providers

### 1. Perplexity AI (Recommended)
- **Get your API key**: https://www.perplexity.ai/settings/api
- **Add to .env**: `PERPLEXITY_API_KEY=your_actual_api_key_here`
- **Models used**: llama-3.1-sonar-small-128k-online

### 2. Claude AI (Anthropic)
- **Get your API key**: https://console.anthropic.com/
- **Add to .env**: `ANTHROPIC_API_KEY=your_actual_api_key_here`
- **Model used**: claude-3-haiku-20240307

### 3. Groq (Llama models)
- **Get your API key**: https://console.groq.com/keys
- **Add to .env**: `GROQ_API_KEY=your_actual_api_key_here`
- **Model used**: llama-3.1-8b-instant

## Important Notes

- You only need **ONE** API key to be configured for the AI features to work
- The app will automatically detect which providers are available
- Do NOT commit your API keys to version control
- The placeholder values (like `your_perplexity_api_key_here`) will not work - you need actual API keys

## Troubleshooting

If you see errors like "No AI provider available", it means:
1. No API keys are configured in your `.env` file
2. The API keys are still placeholder values
3. The API keys are invalid

To fix this, ensure you have at least one valid API key configured in your `.env` file.