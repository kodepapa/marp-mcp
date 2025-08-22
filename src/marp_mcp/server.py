#!/usr/bin/env python3
"""
Marp MCP Server

Exposes Marp CLI functionality through the Model Context Protocol.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("marp-mcp-server")


class MarpConvertParams(BaseModel):
    """Parameters for converting Markdown to slides"""
    markdown: str = Field(..., description="Markdown content with Marp directives")
    output_format: str = Field("html", description="Output format: html, pdf, pptx, png, jpeg")
    theme: Optional[str] = Field(None, description="Theme name: default, gaia, uncover, or custom CSS path")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional Marp CLI options")


class MarpThemeParams(BaseModel):
    """Parameters for listing available themes"""
    include_builtin: bool = Field(True, description="Include built-in themes")


class MarpValidateParams(BaseModel):
    """Parameters for validating Marp markdown"""
    markdown: str = Field(..., description="Markdown content to validate")


async def run_marp_command(args: List[str], input_data: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute Marp CLI command and return results
    """
    try:
        # Ensure marp is available
        result = subprocess.run(
            ["marp", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": "Marp CLI not found. Please install it with: npm install -g @marp-team/marp-cli"
            }
        
        # Run the actual command
        cmd = ["marp"] + args
        logger.info(f"Running command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if input_data else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate(input_data.encode() if input_data else None)
        
        if process.returncode == 0:
            return {
                "success": True,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else ""
            }
        else:
            return {
                "success": False,
                "error": stderr.decode() if stderr else "Command failed",
                "stdout": stdout.decode() if stdout else ""
            }
            
    except Exception as e:
        logger.error(f"Error running Marp command: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available Marp tools"""
    return [
        Tool(
            name="marp_convert",
            description="Convert Markdown to presentation slides using Marp",
            inputSchema={
                "type": "object",
                "properties": {
                    "markdown": {
                        "type": "string",
                        "description": "Markdown content with Marp directives"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["html", "pdf", "pptx", "png", "jpeg"],
                        "default": "html",
                        "description": "Output format for the presentation"
                    },
                    "theme": {
                        "type": "string",
                        "description": "Theme name (default, gaia, uncover) or path to custom CSS"
                    },
                    "options": {
                        "type": "object",
                        "description": "Additional Marp CLI options",
                        "properties": {
                            "allow_local_files": {"type": "boolean"},
                            "html": {"type": "boolean"},
                            "pdf_notes": {"type": "boolean"},
                            "pdf_outlines": {"type": "boolean"}
                        }
                    }
                },
                "required": ["markdown"]
            }
        ),
        Tool(
            name="marp_get_themes",
            description="Get list of available Marp themes",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_builtin": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include built-in themes in the list"
                    }
                }
            }
        ),
        Tool(
            name="marp_validate",
            description="Validate Marp markdown syntax",
            inputSchema={
                "type": "object",
                "properties": {
                    "markdown": {
                        "type": "string",
                        "description": "Markdown content to validate"
                    }
                },
                "required": ["markdown"]
            }
        ),
        Tool(
            name="marp_preview",
            description="Generate a preview of the presentation",
            inputSchema={
                "type": "object",
                "properties": {
                    "markdown": {
                        "type": "string",
                        "description": "Markdown content with Marp directives"
                    },
                    "theme": {
                        "type": "string",
                        "description": "Theme to use for preview"
                    },
                    "slide_number": {
                        "type": "integer",
                        "description": "Specific slide to preview (1-indexed)",
                        "minimum": 1
                    }
                },
                "required": ["markdown"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls"""
    
    if name == "marp_convert":
        params = MarpConvertParams(**arguments)
        
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.md"
            input_file.write_text(params.markdown)
            
            # Determine output file extension
            ext_map = {
                "html": ".html",
                "pdf": ".pdf",
                "pptx": ".pptx",
                "png": ".png",
                "jpeg": ".jpg"
            }
            output_file = Path(tmpdir) / f"output{ext_map.get(params.output_format, '.html')}"
            
            # Build Marp command
            args = [str(input_file), "-o", str(output_file)]
            
            if params.theme:
                args.extend(["--theme", params.theme])
            
            # Add additional options
            if params.options:
                if params.options.get("allow_local_files"):
                    args.append("--allow-local-files")
                if params.options.get("html"):
                    args.append("--html")
                if params.options.get("pdf_notes"):
                    args.append("--pdf-notes")
                if params.options.get("pdf_outlines"):
                    args.append("--pdf-outlines")
            
            result = await run_marp_command(args)
            
            if result["success"] and output_file.exists():
                # Read the output file
                if params.output_format in ["png", "jpeg"]:
                    content = output_file.read_bytes()
                    # Return as base64 encoded image
                    import base64
                    encoded = base64.b64encode(content).decode()
                    return [
                        TextContent(
                            type="text",
                            text=f"Successfully generated {params.output_format.upper()} presentation"
                        ),
                        ImageContent(
                            type="image",
                            data=encoded,
                            mimeType=f"image/{params.output_format}"
                        )
                    ]
                else:
                    content = output_file.read_text() if params.output_format == "html" else None
                    
                    if params.output_format == "html" and content:
                        return [TextContent(
                            type="text",
                            text=f"Successfully generated HTML presentation:\n\n{content}"
                        )]
                    else:
                        # For PDF and PPTX, save to a known location
                        save_path = Path.home() / f"marp_output{ext_map[params.output_format]}"
                        output_file.rename(save_path)
                        return [TextContent(
                            type="text",
                            text=f"Successfully generated {params.output_format.upper()} presentation. Saved to: {save_path}"
                        )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error converting markdown: {result.get('error', 'Unknown error')}"
                )]
    
    elif name == "marp_get_themes":
        # List built-in themes
        themes = [
            {"name": "default", "description": "Default Marp theme"},
            {"name": "gaia", "description": "Gaia theme - gorgeous and modern"},
            {"name": "uncover", "description": "Uncover theme - clean and minimal"}
        ]
        
        return [TextContent(
            type="text",
            text=f"Available Marp themes:\n{json.dumps(themes, indent=2)}"
        )]
    
    elif name == "marp_validate":
        params = MarpValidateParams(**arguments)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "validate.md"
            input_file.write_text(params.markdown)
            
            # Try to convert to HTML to validate
            output_file = Path(tmpdir) / "validate.html"
            args = [str(input_file), "-o", str(output_file)]
            
            result = await run_marp_command(args)
            
            if result["success"]:
                return [TextContent(
                    type="text",
                    text="✅ Markdown is valid Marp syntax"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Validation failed:\n{result.get('error', 'Unknown error')}"
                )]
    
    elif name == "marp_preview":
        markdown = arguments.get("markdown", "")
        theme = arguments.get("theme", "default")
        slide_number = arguments.get("slide_number")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "preview.md"
            input_file.write_text(markdown)
            
            # Generate HTML preview
            output_file = Path(tmpdir) / "preview.html"
            args = [str(input_file), "-o", str(output_file), "--theme", theme]
            
            result = await run_marp_command(args)
            
            if result["success"] and output_file.exists():
                html_content = output_file.read_text()
                
                # Extract preview information
                slides_count = html_content.count('<section')
                
                preview_info = f"""
📊 Presentation Preview:
- Total slides: {slides_count}
- Theme: {theme}
- Format: HTML
                
Preview generated successfully! The HTML contains all slides.
To view specific slide #{slide_number or 1}, open the HTML in a browser.
                """
                
                return [TextContent(
                    type="text",
                    text=preview_info
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error generating preview: {result.get('error', 'Unknown error')}"
                )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def run_server():
    """Run the MCP server"""
    logger.info("Starting Marp MCP Server...")
    
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Main entry point for the MCP server"""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()