"""
Modern Tools for Research Pipeline
Using @tool decorator pattern with improved error handling
"""

from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from typing import Optional
import logging

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Tavily client
try:
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
except Exception as e:
    logger.warning(f"Tavily not initialized: {str(e)}")
    tavily = None


# ============================================
# Web Search Tool (Modern Pattern)
# ============================================

@tool
def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for recent and reliable information.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        Formatted string with titles, URLs, and content snippets
    """
    try:
        if not tavily:
            return "Error: Tavily API not configured. Please set TAVILY_API_KEY environment variable."
        
        results = tavily.search(query=query, max_results=max_results)
        
        if not results.get('results'):
            return f"No search results found for: {query}"
        
        formatted_results = []
        
        for idx, result in enumerate(results['results'], 1):
            title = result.get('title', 'N/A')
            url = result.get('url', 'N/A')
            content = result.get('content', '')[:300]  # Limit snippet length
            score = result.get('score', 0)
            
            formatted_result = (
                f"[{idx}] TITLE: {title}\n"
                f"    URL: {url}\n"
                f"    CONTENT: {content}\n"
                f"    RELEVANCE SCORE: {score:.2f}\n"
            )
            formatted_results.append(formatted_result)
        
        return "\n----\n".join(formatted_results)
    
    except Exception as e:
        error_msg = f"Search error: {str(e)}"
        logger.error(error_msg)
        return error_msg


# ============================================
# URL Scraping Tool (Modern Pattern)
# ============================================

@tool
def scrape_url(url: str, max_length: int = 5000) -> str:
    """
    Scrape and extract clean text content from a URL.
    
    Args:
        url: URL to scrape
        max_length: Maximum characters to return (default: 5000)
    
    Returns:
        Clean extracted text content from the webpage
    """
    try:
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            return f"Invalid URL format: {url}"
        
        # Make request with proper headers and timeout
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(
            url,
            timeout=10,
            headers=headers,
            allow_redirects=True
        )
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe', 'ad']):
            element.decompose()
        
        # Extract text
        text = soup.get_text(separator=" ", strip=True)
        
        # Clean up whitespace
        text = " ".join(text.split())
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length] + "... [truncated]"
        
        if not text.strip():
            return f"No readable content found at: {url}"
        
        return text
    
    except requests.exceptions.Timeout:
        return f"Timeout: URL took too long to respond: {url}"
    except requests.exceptions.ConnectionError:
        return f"Connection error: Could not reach URL: {url}"
    except requests.exceptions.HTTPError as e:
        status_code = getattr(e.response, "status_code", "unknown") if e.response is not None else "unknown"
        return f"HTTP error {status_code}: {url}"
    except Exception as e:
        error_msg = f"Scraping error for {url}: {str(e)}"
        logger.error(error_msg)
        return error_msg


# ============================================
# Advanced: Citation Extractor Tool
# ============================================

@tool
def extract_urls(text: str) -> str:
    """
    Extract all URLs from text content.
    
    Args:
        text: Text content to extract URLs from
    
    Returns:
        Formatted list of unique URLs found
    """
    import re
    
    try:
        # Regex pattern for URLs
        url_pattern = r'https?://[^\s\]]+|www\.[^\s\]]+'
        urls = re.findall(url_pattern, text)
        
        # Remove duplicates and sort
        unique_urls = sorted(list(set(urls)))
        
        if not unique_urls:
            return "No URLs found in text."
        
        formatted_urls = "\n".join([f"• {url}" for url in unique_urls])
        return f"Found {len(unique_urls)} unique URLs:\n\n{formatted_urls}"
    
    except Exception as e:
        return f"Error extracting URLs: {str(e)}"


# ============================================
# Tool Collection Export
# ============================================

tools = [web_search, scrape_url, extract_urls]

__all__ = ['web_search', 'scrape_url', 'extract_urls', 'tools']