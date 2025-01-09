from typing import List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

from .types import Document
from .confluence import ConfluenceFetcher
from .jira import JiraFetcher

logger = logging.getLogger("mcp-atlassian")


@dataclass
class SearchResult:
    """Unified search result structure for both Confluence and Jira."""

    id: str  # page_id for Confluence, issue_key for Jira
    title: str
    content: str
    url: str
    platform: str  # 'confluence' or 'jira'
    last_modified: str
    content_type: str  # 'page', 'issue', etc.
    space_or_project: str  # space_key for Confluence, project_key for Jira
    author: Optional[str] = None


class UnifiedSearch:
    """Handles unified search across Confluence and Jira platforms."""

    def __init__(
        self, confluence_fetcher: ConfluenceFetcher, jira_fetcher: JiraFetcher
    ):
        self.confluence = confluence_fetcher
        self.jira = jira_fetcher

    def _search_confluence(self, query: str, limit: int = 25) -> List[SearchResult]:
        """Search Confluence content."""
        try:
            # Convert query to CQL if needed
            cql = f'type=page AND text ~ "{query}"'
            documents = self.confluence.search(cql, limit=limit)

            results = []
            for doc in documents:
                results.append(
                    SearchResult(
                        id=doc.metadata["page_id"],
                        title=doc.metadata["title"],
                        content=(
                            doc.page_content[:500] + "..."
                            if len(doc.page_content) > 500
                            else doc.page_content
                        ),
                        url=doc.metadata["url"],
                        platform="confluence",
                        last_modified=doc.metadata.get("last_modified", ""),
                        content_type="page",
                        space_or_project=doc.metadata.get("space_key", ""),
                        author=doc.metadata.get("author_name"),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Error searching Confluence: {e}")
            return []

    def _search_jira(self, query: str, limit: int = 25) -> List[SearchResult]:
        """Search Jira issues."""
        try:
            # Convert query to JQL if needed
            jql = f'text ~ "{query}"'
            documents = self.jira.search_issues(jql, limit=limit)

            results = []
            for doc in documents:
                results.append(
                    SearchResult(
                        id=doc.metadata["key"],
                        title=doc.metadata["title"],
                        content=(
                            doc.page_content[:500] + "..."
                            if len(doc.page_content) > 500
                            else doc.page_content
                        ),
                        url=doc.metadata["link"],
                        platform="jira",
                        last_modified=doc.metadata.get("created_date", ""),
                        content_type=doc.metadata.get("type", "issue").lower(),
                        space_or_project=doc.metadata["key"].split("-")[0],
                        author=None,  # Could be enhanced to include reporter/assignee
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Error searching Jira: {e}")
            return []

    def search(
        self, query: str, platforms: Optional[List[str]] = None, limit: int = 50
    ) -> List[SearchResult]:
        """
        Perform unified search across both platforms.

        Args:
            query: Search query string
            platforms: Optional list of platforms to search ('confluence', 'jira')
            limit: Maximum total results to return (split between platforms)

        Returns:
            List of SearchResult objects containing matched content
        """
        if platforms is None:
            platforms = ["confluence", "jira"]

        per_platform_limit = limit // len(platforms)

        results = []
        with ThreadPoolExecutor(max_workers=len(platforms)) as executor:
            futures = []

            if "confluence" in platforms:
                futures.append(
                    executor.submit(self._search_confluence, query, per_platform_limit)
                )
            if "jira" in platforms:
                futures.append(
                    executor.submit(self._search_jira, query, per_platform_limit)
                )

            for future in futures:
                try:
                    results.extend(future.result())
                except Exception as e:
                    logger.error(f"Error in search execution: {e}")

        # Sort results by last_modified date if available
        results.sort(
            key=lambda x: (
                datetime.fromisoformat(x.last_modified.replace("Z", "+00:00"))
                if x.last_modified
                else datetime.min
            ),
            reverse=True,
        )

        return results[:limit]
