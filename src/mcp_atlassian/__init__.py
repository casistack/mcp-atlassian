"""MCP Atlassian Integration Package"""

import os

import asyncio

from . import server

if not os.getenv("TESTING"):
    from . import server
    from .config import Config
    from .confluence import ConfluenceFetcher
    from .jira import JiraFetcher
    from .search import UnifiedSearch
    from .types import *

__version__ = "0.1.7"


def main():
    """Main entry point for the package."""
    asyncio.run(server.main())


__all__ = ["main", "server", "__version__"]
