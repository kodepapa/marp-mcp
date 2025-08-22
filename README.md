# Marp MCP Server

An MCP (Model Context Protocol) server that exposes [Marp CLI](https://github.com/marp-team/marp-cli) functionality to AI agents, enabling them to create beautiful presentations from Markdown.

## Features

- **Convert Markdown to Presentations**: Generate HTML, PDF, PPTX, PNG, or JPEG presentations
- **Theme Support**: Use built-in themes (default, gaia, uncover) or custom CSS
- **Validation**: Check Marp markdown syntax
- **Preview Generation**: Preview presentations before final export
- **Full Marp CLI Options**: Access to additional options like PDF notes, outlines, etc.

## Installation

### Prerequisites

1. Install Marp CLI via npm:
```bash
npm install -g @marp-team/marp-cli
```

### Setup

The easiest way to use this server is via uvx (recommended):

```bash
uvx --from git+https://github.com/YOUR_USERNAME/marp-mcp-server.git@main marp-mcp-server
```

Or clone and install locally:

```bash
git clone <your-repo-url>
cd marp-mcp-server
uv sync
uv run marp-mcp
```

## Usage

### MCP Client Configuration

For Claude Desktop or other MCP clients, add to your configuration:

```json
{
  "mcpServers": {
    "marp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/YOUR_USERNAME/marp-mcp-server.git@main",
        "marp-mcp-server"
      ]
    }
  }
}
```

### Available Tools

#### 1. `marp_convert`
Convert Markdown to various presentation formats.

**Parameters:**
- `markdown` (required): Markdown content with Marp directives
- `output_format`: Output format (html, pdf, pptx, png, jpeg)
- `theme`: Theme name or custom CSS path
- `options`: Additional Marp CLI options

**Example:**
```json
{
  "tool": "marp_convert",
  "arguments": {
    "markdown": "---\nmarp: true\ntheme: gaia\n---\n\n# Hello World\n\nThis is a Marp presentation",
    "output_format": "pdf",
    "theme": "gaia"
  }
}
```

#### 2. `marp_get_themes`
Get list of available Marp themes.

**Parameters:**
- `include_builtin`: Include built-in themes (default: true)

#### 3. `marp_validate`
Validate Marp markdown syntax.

**Parameters:**
- `markdown` (required): Markdown content to validate

#### 4. `marp_preview`
Generate a preview of the presentation.

**Parameters:**
- `markdown` (required): Markdown content
- `theme`: Theme to use
- `slide_number`: Specific slide to preview

## Example Marp Markdown

```markdown
---
marp: true
theme: gaia
paginate: true
---

# My Presentation

Welcome to my Marp presentation!

---

## Slide 2

- Bullet point 1
- Bullet point 2
- Bullet point 3

---

## Code Example

\`\`\`python
def hello_world():
    print("Hello, Marp!")
\`\`\`

---

# Thank You!
```

## Development

### Running Tests

```bash
uv run pytest
```

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd marp-mcp-server
```

2. Install dependencies:
```bash
uv sync
```

3. Run the server:
```bash
uv run marp-mcp
```

### Adding New Features

1. Add new tool definitions in `list_tools()`
2. Implement tool logic in `call_tool()`
3. Update README with new tool documentation

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.