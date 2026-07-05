import re
import requests
from bs4 import BeautifulSoup

def extract_youtube_video_id(url: str) -> str | None:
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def scrape_article(url: str) -> dict:
    """Fetches and extracts the main text content from a news article, web page, or YouTube URL (transcript).

    Args:
        url: The absolute web URL of the article or video to scrape.

    Returns:
        A dictionary containing the status, title, and cleaned content of the page or transcript.
    """
    video_id = extract_youtube_video_id(url)
    if video_id:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.list(video_id)
            first_transcript = next(iter(transcript_list))
            transcript_data = first_transcript.fetch()
            transcript_text = " ".join([item.text for item in transcript_data])
            return {
                "status": "success",
                "title": f"YouTube Video Transcript (ID: {video_id})",
                "content": transcript_text
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to extract YouTube transcript for video {video_id}: {str(e)}. Make sure transcripts are enabled/public for this video."
            }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        # Get title
        title = soup.title.string.strip() if soup.title else "Untitled Article"
        
        # Try to find article body or just gather paragraph text
        article_body = soup.find("article")
        if article_body:
            paragraphs = article_body.find_all("p")
        else:
            paragraphs = soup.find_all("p")
            
        text_content = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        # Clean whitespace
        text_content = re.sub(r'\n{3,}', '\n\n', text_content)
        
        if len(text_content) < 100:
            # Fallback to general body text extraction if paragraph text is too short
            body_text = soup.get_text(separator="\n\n")
            lines = [line.strip() for line in body_text.splitlines() if line.strip()]
            text_content = "\n\n".join(lines)
            
        # Truncate content to avoid token blowup (limit to 10k chars)
        if len(text_content) > 10000:
            text_content = text_content[:10000] + "\n\n[...Content truncated due to length...]"
            
        return {
            "status": "success",
            "title": title,
            "content": text_content
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to scrape URL: {str(e)}"
        }

def search_web(query: str) -> dict:
    """Searches the web for the given query and returns snippet results.
    Use this to research entities, organizations, and funding sources.

    Args:
        query: The search query string.

    Returns:
        A dictionary containing the status and list of result snippets.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        # Parse DuckDuckGo html search results
        for link in soup.find_all("a", class_="result__url"):
            parent = link.find_parent("div", class_="result__body")
            if not parent:
                continue
            
            title_elem = parent.find("a", class_="result__snippet")
            snippet_elem = parent.find("a", class_="result__snippet")
            
            title = parent.find("h2", class_="result__title").get_text().strip() if parent.find("h2", class_="result__title") else ""
            snippet = snippet_elem.get_text().strip() if snippet_elem else ""
            href = link.get("href", "")
            
            # Extract actual URL from DDG redirect url
            match = re.search(r'uddg=(https?%3A%2F%2F[^&]+)', href)
            if match:
                href = requests.utils.unquote(match.group(1))
                
            if title and snippet:
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "url": href
                })
                
            if len(results) >= 5:
                break
                
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to perform search: {str(e)}"
        }

