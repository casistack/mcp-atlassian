from dataclasses import dataclass


@dataclass
class ConfluenceConfig:
    """Confluence API configuration."""

    url: str  # Base URL for Confluence
    username: str  # Email or username
    api_token: str  # API token used as password

    @property
    def is_cloud(self) -> bool:
        """Check if this is a cloud instance."""
        return "atlassian.net" in self.url


@dataclass
class JiraConfig:
    """Jira API configuration."""

    url: str  # Base URL for Jira
    username: str  # Email or username
    api_token: str  # API token used as password

    @property
    def is_cloud(self) -> bool:
        """Check if this is a cloud instance."""
        return "atlassian.net" in self.url


@dataclass
class Config:
    """Combined configuration for Atlassian services."""

    confluence: ConfluenceConfig
    jira: JiraConfig

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        import os
        from dotenv import load_dotenv

        load_dotenv()

        confluence_config = ConfluenceConfig(
            url=os.getenv("CONFLUENCE_URL", ""),
            username=os.getenv("CONFLUENCE_USERNAME", ""),
            api_token=os.getenv("CONFLUENCE_API_TOKEN", ""),
        )

        jira_config = JiraConfig(
            url=os.getenv("JIRA_URL", ""),
            username=os.getenv("JIRA_USERNAME", ""),
            api_token=os.getenv("JIRA_API_TOKEN", ""),
        )

        return cls(confluence=confluence_config, jira=jira_config)
