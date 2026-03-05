---
name: "github-trending"
description: "Query GitHub trending repositories. Invoke when user wants to see what's popular on GitHub, find trending projects, or discover hot open-source repositories by language or time range."
---

# github-trending

Query GitHub trending repositories by scraping the GitHub Trending page. Discover what's hot in the open-source community.

## Usage

### List Trending Repositories
Get the current trending repositories on GitHub.

```bash
python3 skills/github-trending/github_trending.py
```

### Filter by Language
Filter trending repositories by programming language.

```bash
python3 skills/github-trending/github_trending.py -l python
python3 skills/github-trending/github_trending.py -l javascript
python3 skills/github-trending/github_trending.py -l rust
```

### Filter by Time Range
Filter by daily, weekly, or monthly trends.

```bash
python3 skills/github-trending/github_trending.py -s daily
python3 skills/github-trending/github_trending.py -s weekly
python3 skills/github-trending/github_trending.py -s monthly
```

### Filter by Spoken Language
Filter by natural language of the repository.

```bash
python3 skills/github-trending/github_trending.py --spoken-language zh
python3 skills/github-trending/github_trending.py --spoken-language en
```

### Combined Filters
Combine language and time range filters.

```bash
python3 skills/github-trending/github_trending.py -l typescript -s weekly
```

### Limit Results
Limit the number of results returned.

```bash
python3 skills/github-trending/github_trending.py -n 10
```

### Output Formats
Output results in different formats.

```bash
python3 skills/github-trending/github_trending.py -f json
python3 skills/github-trending/github_trending.py -f markdown
python3 skills/github-trending/github_trending.py -f simple
```

### Save to File
Save results to a file.

```bash
python3 skills/github-trending/github_trending.py -o trending.md
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `-l, --language` | No | all | Programming language filter (e.g., python, javascript, rust, go) |
| `-s, --since` | No | daily | Time range: `daily`, `weekly`, or `monthly` |
| `--spoken-language` | No | all | Natural language filter (e.g., zh, en) |
| `-n, --number` | No | 10 | Maximum number of results to return |
| `-f, --format` | No | simple | Output format: `simple`, `json`, or `markdown` |
| `-o, --output` | No | stdout | Output file path |

## Output

Each result includes:
- `name`: Full repository name (owner/repo)
- `url`: GitHub URL
- `author`: Repository owner
- `repo`: Repository name
- `description`: Repository description
- `language`: Primary programming language
- `stars`: Total star count
- `forks`: Total fork count
- `stars_today`: Stars gained today

## Data Source

Scrapes GitHub Trending page directly from: https://github.com/trending

## Dependencies

- Python 3.x
- requests
- beautifulsoup4

Install dependencies:
```bash
pip install requests beautifulsoup4
```

## Examples

### Quick Check
```bash
python3 skills/github-trending/github_trending.py -n 5
```

### Python Weekly Trends
```bash
python3 skills/github-trending/github_trending.py -l python -s weekly -n 10
```

### Rust Monthly Stars
```bash
python3 skills/github-trending/github_trending.py -l rust -s monthly
```

### Export as Markdown
```bash
python3 skills/github-trending/github_trending.py -f markdown -o trending.md
```

### JSON Output for Processing
```bash
python3 skills/github-trending/github_trending.py -f json -n 20
```
