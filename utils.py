import re
from urllib.parse import urlparse

def is_valid_url(url):
    """
    Check if a URL is valid.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    if not url:
        return False
    
    # Basic URL validation
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except:
        return False

def format_dailymotion_url(url):
    """
    Format the Dailymotion URL to ensure it's in a consistent format.
    
    Args:
        url (str): Dailymotion URL to format
        
    Returns:
        str: Formatted Dailymotion URL
    """
    if not url:
        return url
    
    # Handle dai.ly short URLs
    if 'dai.ly' in url:
        video_id = re.search(r'dai\.ly/([a-zA-Z0-9]+)', url)
        if video_id:
            return f"https://www.dailymotion.com/video/{video_id.group(1)}"
    
    # Handle embed URLs
    if '/embed/' in url:
        video_id = re.search(r'dailymotion\.com/embed/video/([a-zA-Z0-9]+)', url)
        if video_id:
            return f"https://www.dailymotion.com/video/{video_id.group(1)}"
    
    return url
