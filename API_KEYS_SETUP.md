# API Keys Setup for AIRO Response Collection

To collect responses from AI platforms, you need to set up API keys.

## Required API Keys

You need at least ONE of these (all three recommended):

### 1. Anthropic (Claude)
- Get key from: https://console.anthropic.com/
- Cost: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- Best for: High-quality, detailed responses

### 2. OpenAI (ChatGPT)
- Get key from: https://platform.openai.com/api-keys
- Cost: GPT-4o ~$2.50 per 1M input tokens, ~$10 per 1M output tokens
- Best for: General queries, fast responses

### 3. Google (Gemini)
- Get key from: https://makersuite.google.com/app/apikey
- Cost: Gemini Pro is FREE up to 60 requests/minute
- Best for: Testing, high-volume queries

## Setup Instructions

### Option 1: Environment Variables (Temporary - Current Session Only)

```bash
# In your terminal:
export ANTHROPIC_API_KEY='sk-ant-api03-...'
export OPENAI_API_KEY='sk-proj-...'
export GOOGLE_API_KEY='AIza...'
```

Then run the collection script:
```bash
./venv/bin/python collect_responses.py
```

### Option 2: Add to Shell Profile (Permanent)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# AIRO API Keys
export ANTHROPIC_API_KEY='sk-ant-api03-...'
export OPENAI_API_KEY='sk-proj-...'
export GOOGLE_API_KEY='AIza...'
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Option 3: .env File (Recommended for Development)

Create a `.env` file in the project root:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...
GOOGLE_API_KEY=AIza...
```

Then load it before running:
```bash
set -a; source .env; set +a
./venv/bin/python collect_responses.py
```

## Cost Estimates

For 22 queries across 3 platforms (66 total API calls):

- **OpenAI GPT-4o**: ~$0.10-0.15 per run
- **Anthropic Claude**: ~$0.15-0.20 per run
- **Google Gemini**: FREE (within rate limits)

**Total per run: ~$0.25-0.35** (or FREE with Gemini only)

## Testing First

Start with a test run:

```bash
./venv/bin/python collect_responses.py
# Choose option 2: "Test with first 3 queries only"
```

This will only cost a few cents and verify everything works.

## Troubleshooting

**"No API keys found"**:
- Make sure you've exported the variables in your current terminal
- Check with: `echo $ANTHROPIC_API_KEY`

**"Rate limit exceeded"**:
- The script includes 1-second delays between requests
- For Google: Max 60 requests/minute (we stay well under this)

**"Invalid API key"**:
- Double-check you copied the full key
- Make sure there are no extra spaces or quotes
- Keys should start with: `sk-ant-` (Anthropic), `sk-proj-` (OpenAI), `AIza` (Google)

## Running Collection

```bash
# Test with 3 queries
./venv/bin/python collect_responses.py
# Choose option 2

# Full collection (all 22 queries)
./venv/bin/python collect_responses.py
# Choose option 1
```

## What Happens Next

1. Script queries each platform with each query
2. Responses are saved to the database
3. You can view them at: http://localhost:5173/data/responses
4. Dashboard will show real metrics at: http://localhost:5173/
5. Analytics pages will have real data

## Analysis (Next Step)

After collecting responses, you'll need to analyze them to:
- Detect PPPL mentions
- Assess sentiment
- Extract descriptors
- Identify competitors mentioned

This can be done manually or with another AI-powered analysis script (coming soon).
