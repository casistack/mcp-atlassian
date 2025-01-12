import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

from mcp_atlassian.confluence import ConfluenceFetcher


async def main():
    fetcher = ConfluenceFetcher()
    templates = fetcher.get_templates(space_key="IS")
    print("Templates response:", json.dumps(templates, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
