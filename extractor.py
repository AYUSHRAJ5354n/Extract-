import logging
import time
import re
import os
import traceback
import warnings
import requests
from urllib.parse import urlparse, urljoin

# Try to import selenium components, but don't fail if they're not available
# This allows the code to run in environments where selenium can't be properly initialized
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    # Define placeholder classes to avoid errors
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium not available, will use non-browser extraction methods only")

# Configure logging
logger = logging.getLogger(__name__)

# Maximum retries and timeouts
MAX_RETRIES = 3
PAGE_LOAD_TIMEOUT = 30
ELEMENT_WAIT_TIMEOUT = 15

def setup_webdriver():
    """Set up and return a headless Chrome webdriver configured for cloud environments"""
    
    # If Selenium is not available, return None immediately
    if not SELENIUM_AVAILABLE:
        logger.warning("Selenium not available, skipping browser setup")
        return None
    
    try:
        # Import additional components for better cloud compatibility
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            webdriver_manager_available = True
        except ImportError:
            webdriver_manager_available = False
            logger.warning("WebDriver Manager not available, will use fallback methods")
        
        # Create Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--remote-debugging-port=9222")  # Required for some cloud environments
        
        # Add user agent to avoid bot detection
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36")
        
        # Try multiple methods to initialize the driver
        
        # Method 1: Use WebDriver Manager (works well on various cloud platforms)
        if webdriver_manager_available:
            try:
                logger.info("Attempting to create Chrome driver with WebDriver Manager")
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
                logger.info("Successfully created Chrome driver with WebDriver Manager")
                return driver
            except Exception as e:
                logger.warning(f"WebDriver Manager method failed: {str(e)}")
        
        # Method 2: Standard initialization
        try:
            logger.info("Attempting to create Chrome driver with default settings")
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            logger.info("Successfully created Chrome driver with default settings")
            return driver
        except Exception as e:
            logger.warning(f"Error creating Chrome driver with default settings: {str(e)}")
        
        # Method 3: For Koyeb, Docker and some cloud environments
        try:
            logger.info("Attempting Koyeb/Docker compatible Chrome driver setup")
            chrome_options.binary_location = "/usr/bin/google-chrome"
            if webdriver_manager_available:
                service = Service("/usr/bin/chromedriver")
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            logger.info("Successfully created Chrome driver with Koyeb/Docker compatibility")
            return driver
        except Exception as e2:
            logger.warning(f"Koyeb/Docker method failed: {str(e2)}")
        
        # Method 4: For Replit and similar environments
        try:
            logger.info("Attempting Replit-compatible Chrome driver setup")
            chrome_options.binary_location = "/usr/bin/google-chrome-stable"
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            logger.info("Successfully created Chrome driver with Replit compatibility")
            return driver
        except Exception as e3:
            logger.error(f"All driver creation methods failed. Last error: {str(e3)}")
            logger.error("Falling back to non-browser extraction methods")
            return None
    except Exception as e:
        logger.error(f"Error setting up webdriver: {str(e)}")
        return None

def fetch_url_content(url):
    """Fetch URL content without using a browser"""
    # Suppress InsecureRequestWarning
    warnings.filterwarnings('ignore', 'Unverified HTTPS request')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Error fetching URL content: {str(e)}")
        return None

def extract_from_lucifer_direct(url, html_content=None):
    """
    Extract Dailymotion link from Lucifer Donghua site without using browser
    """
    logger.info(f"Direct extraction from Lucifer Donghua URL: {url}")
    
    if not html_content:
        html_content = fetch_url_content(url)
        if not html_content:
            return {'success': False, 'error': "Failed to fetch Lucifer Donghua page content"}
    
    try:
        # First extract any direct dailymotion links
        dailymotion_links = extract_dailymotion_from_source(html_content)
        if dailymotion_links:
            logger.info(f"Found Dailymotion link in Lucifer Donghua page source: {dailymotion_links[0]}")
            return {'success': True, 'link': dailymotion_links[0]}
        
        # Look for server selection dropdown (specific to Lucifer Donghua site)
        # <option value="https://luciferdonghua.in/swallowed-star-season-4-episode-83-168-lucifer-donghua/v/1/" data-index="1">Dailymotion [ENG SUB]</option>
        dailymotion_server_pattern = r'<option value="([^"]*)"[^>]*>.*?[Dd]ailymotion.*?</option>'
        dailymotion_server_matches = re.findall(dailymotion_server_pattern, html_content, re.DOTALL)
        
        for server_url in dailymotion_server_matches:
            # If URL is relative, convert to absolute
            if not server_url.startswith('http'):
                if server_url.startswith('//'):
                    server_url = f"https:{server_url}"
                else:
                    base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
                    server_url = urljoin(base_url, server_url)
            
            logger.info(f"Found Dailymotion server option in dropdown, loading: {server_url}")
            server_content = fetch_url_content(server_url)
            
            if server_content:
                # Extract Dailymotion links from this server page
                server_dm_links = extract_dailymotion_from_source(server_content)
                if server_dm_links:
                    return {'success': True, 'link': server_dm_links[0]}
                
                # Check for iframes in this server page
                iframe_pattern = r'<iframe[^>]*src="([^"]*)"[^>]*>'
                server_iframes = re.findall(iframe_pattern, server_content)
                
                for iframe_src in server_iframes:
                    if 'dailymotion' in iframe_src or 'dai.ly' in iframe_src:
                        return {'success': True, 'link': clean_dailymotion_url(iframe_src)}
        
        # If no specific Dailymotion server found, look for the /v/ pattern in URLs
        # Lucifer sites often use URL patterns like /v/1/ for server 1
        v_pattern_urls = []
        for i in range(1, 6):  # Try servers 1-5
            v_url = f"{url.rstrip('/')}/v/{i}/"
            v_pattern_urls.append(v_url)
        
        for v_url in v_pattern_urls:
            logger.info(f"Trying Lucifer Donghua numbered server: {v_url}")
            v_content = fetch_url_content(v_url)
            
            if v_content:
                v_dm_links = extract_dailymotion_from_source(v_content)
                if v_dm_links:
                    return {'success': True, 'link': v_dm_links[0]}
                
                # Check for iframes with Dailymotion content
                v_iframes = re.findall(r'<iframe[^>]*src="([^"]*)"[^>]*>', v_content)
                for v_iframe in v_iframes:
                    if 'dailymotion' in v_iframe or 'dai.ly' in v_iframe:
                        return {'success': True, 'link': clean_dailymotion_url(v_iframe)}
        
        # Look for server options in any format
        server_sections_pattern = r'<div[^>]*class="[^"]*servers?[^"]*"[^>]*>(.*?)</div>'
        server_sections = re.findall(server_sections_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for section in server_sections:
            # Look for any link or button containing "daily"
            daily_links = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>.*?[Dd]aily.*?</a>', section, re.DOTALL)
            for link in daily_links:
                if not link.startswith('http'):
                    base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
                    link = urljoin(base_url, link)
                
                logger.info(f"Found Dailymotion server link, trying: {link}")
                link_content = fetch_url_content(link)
                if link_content:
                    link_dm_urls = extract_dailymotion_from_source(link_content)
                    if link_dm_urls:
                        return {'success': True, 'link': link_dm_urls[0]}
        
        # Look for all iframes as a fallback
        iframe_pattern = r'<iframe[^>]*src="([^"]*)"[^>]*>'
        iframes = re.findall(iframe_pattern, html_content)
        
        for iframe_src in iframes:
            logger.info(f"Found iframe in Lucifer Donghua: {iframe_src}")
            
            # If it's a direct Dailymotion link
            if 'dailymotion' in iframe_src or 'dai.ly' in iframe_src:
                return {'success': True, 'link': clean_dailymotion_url(iframe_src)}
            
            # If it's a relative URL
            if not iframe_src.startswith('http'):
                if iframe_src.startswith('//'):
                    iframe_src = f"https:{iframe_src}"
                else:
                    # Convert relative URL to absolute
                    base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
                    iframe_src = urljoin(base_url, iframe_src)
            
            # Fetch the iframe content to check for Dailymotion
            iframe_content = fetch_url_content(iframe_src)
            if iframe_content:
                iframe_dm_links = extract_dailymotion_from_source(iframe_content)
                if iframe_dm_links:
                    return {'success': True, 'link': iframe_dm_links[0]}
        
        # Look for the Dailymotion server URL directly in the page
        dailymotion_url_pattern = r'/v/\d+/\?server=dm'
        dm_server_matches = re.findall(dailymotion_url_pattern, html_content)
        
        if dm_server_matches:
            for dm_path in dm_server_matches:
                base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
                dm_url = urljoin(base_url, dm_path)
                
                logger.info(f"Found direct DM server URL: {dm_url}")
                dm_content = fetch_url_content(dm_url)
                
                if dm_content:
                    dm_links = extract_dailymotion_from_source(dm_content)
                    if dm_links:
                        return {'success': True, 'link': dm_links[0]}
        
        # Try the first server URL specifically for Dailymotion
        first_server_url = f"{url.rstrip('/')}/v/1/"
        logger.info(f"Trying first server as last resort: {first_server_url}")
        first_server_content = fetch_url_content(first_server_url)
        
        if first_server_content:
            fs_links = extract_dailymotion_from_source(first_server_content)
            if fs_links:
                return {'success': True, 'link': fs_links[0]}
            
            # Check one more time with v=1 parameter
            v1_url = f"{url.split('?')[0]}?v=1"
            v1_content = fetch_url_content(v1_url)
            if v1_content:
                v1_links = extract_dailymotion_from_source(v1_content)
                if v1_links:
                    return {'success': True, 'link': v1_links[0]}
        
        return {'success': False, 'error': "No Dailymotion content found on Lucifer Donghua page"}
    
    except Exception as e:
        logger.error(f"Error in Lucifer Donghua specialized extraction: {str(e)}")
        logger.error(traceback.format_exc())
        return {'success': False, 'error': f"Failed to extract Dailymotion link from Lucifer Donghua: {str(e)}"}

def extract_dailymotion_link(url):
    """
    Main function to extract Dailymotion links from supported websites
    
    Args:
        url (str): URL of the website to extract links from
        
    Returns:
        dict: Result containing success status and either the link or error message
    """
    driver = None
    try:
        logger.info(f"Starting extraction from URL: {url}")
        
        # Extract domain for site-specific handling
        domain = urlparse(url).netloc.lower()
        
        # Special handling for sites that work better with direct HTML parsing
        if 'seatv' in domain or 'perfect-world' in url.lower():
            logger.info("Detected SeaTV site, using direct extraction")
            return extract_seatv_direct(url)
        
        if 'luciferdonghua' in domain:
            logger.info("Detected Lucifer Donghua site, using direct extraction")
            return extract_from_lucifer_direct(url)
            
        # Try browser-based extraction if possible
        driver = setup_webdriver()
        
        # If driver creation failed, use alternative non-browser method
        if driver is None:
            logger.info("Browser automation not available, using alternative extraction method")
            return extract_without_browser(url)
        
        # Determine which website we're dealing with
        if 'lucifer' in domain:
            return extract_from_lucifer(driver, url)
        elif 'wetv' in domain or 'we.tv' in domain:
            return extract_from_wetv(driver, url)
        else:
            # Try generic extraction if site is not specifically supported
            logger.warning(f"Website {domain} not specifically supported, trying generic extraction")
            return extract_generic(driver, url)
            
    except Exception as e:
        logger.error(f"Error extracting Dailymotion link: {str(e)}")
        logger.error(traceback.format_exc())
        # If browser extraction fails, try non-browser method as fallback
        try:
            logger.info("Attempting non-browser extraction as fallback")
            return extract_without_browser(url)
        except Exception as e2:
            logger.error(f"Non-browser extraction also failed: {str(e2)}")
            return {
                'success': False,
                'error': f"Failed to extract link: {str(e)}"
            }
    finally:
        if driver:
            driver.quit()
            
def extract_seatv_direct(url):
    """
    Specialized function for SeaTV-like sites that directly extracts
    without using a browser
    """
    logger.info(f"Direct extraction from SeaTV URL: {url}")
    
    try:
        # Fetch the page content
        html_content = fetch_url_content(url)
        if not html_content:
            return {'success': False, 'error': "Failed to fetch SeaTV page content"}
            
        # Look for Dailymotion iframes directly
        iframe_patterns = [
            r'<iframe[^>]*src="([^"]*dailymotion[^"]*)"[^>]*>',
            r'<iframe[^>]*src="([^"]*dai\.ly[^"]*)"[^>]*>',
            r'<iframe[^>]*data-src="([^"]*dailymotion[^"]*)"[^>]*>'
        ]
        
        for pattern in iframe_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                for match in matches:
                    if match:
                        # Clean and return the first match
                        return {'success': True, 'link': clean_dailymotion_url(match)}
        
        # If no direct Dailymotion iframes, check for video player sections
        player_section_patterns = [
            r'<div[^>]*class="[^"]*player[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*video[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*id="[^"]*player[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern in player_section_patterns:
            sections = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            for section in sections:
                # Look for Dailymotion links in this section
                dailymotion_links = extract_dailymotion_from_source(section)
                if dailymotion_links:
                    return {'success': True, 'link': dailymotion_links[0]}
                    
                # Look for any iframe that might load a player
                iframe_matches = re.findall(r'<iframe[^>]*src="([^"]*)"[^>]*>', section, re.IGNORECASE)
                for iframe_src in iframe_matches:
                    # Handle iframe URLs that might be player loaders
                    if iframe_src and 'player' in iframe_src.lower():
                        iframe_content = fetch_url_content(iframe_src)
                        if iframe_content:
                            iframe_dailymotion_links = extract_dailymotion_from_source(iframe_content)
                            if iframe_dailymotion_links:
                                return {'success': True, 'link': iframe_dailymotion_links[0]}
        
        # Check for scripts that contain player configuration
        script_patterns = [
            r'<script[^>]*>(.*?var\s+player\s*=.*?)</script>',
            r'<script[^>]*>(.*?videoPlayer.*?)</script>',
            r'<script[^>]*>(.*?dailymotion.*?)</script>'
        ]
        
        for pattern in script_patterns:
            script_matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            for script in script_matches:
                if 'dailymotion' in script.lower() or 'dai.ly' in script.lower():
                    # Look for video IDs in the script
                    for id_pattern in [r'"video":\s*"([a-zA-Z0-9]+)"', r'video[\'"]:\s*[\'"]([a-zA-Z0-9]+)[\'"]']:
                        video_ids = re.findall(id_pattern, script)
                        for video_id in video_ids:
                            if video_id and len(video_id) > 5:  # Valid DM IDs are generally 6+ chars
                                return {'success': True, 'link': f"https://www.dailymotion.com/video/{video_id}"}
        
        # As a last resort, try scanning all iframes
        all_iframes = re.findall(r'<iframe[^>]*src="([^"]*)"[^>]*>', html_content, re.IGNORECASE)
        for iframe_src in all_iframes:
            logger.info(f"Found iframe in SeaTV: {iframe_src}")
            
            # Follow the iframe source to look for Dailymotion content
            if iframe_src and iframe_src.strip():
                try:
                    if not iframe_src.startswith('http'):
                        if iframe_src.startswith('//'):
                            iframe_src = f"https:{iframe_src}"
                        else:
                            # Try to build a full URL from relative URL
                            base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
                            iframe_src = urljoin(base_url, iframe_src)
                    
                    iframe_content = fetch_url_content(iframe_src)
                    if iframe_content:
                        iframe_dailymotion_links = extract_dailymotion_from_source(iframe_content)
                        if iframe_dailymotion_links:
                            return {'success': True, 'link': iframe_dailymotion_links[0]}
                except Exception as e:
                    logger.error(f"Error processing iframe at {iframe_src}: {str(e)}")
        
        # If all else fails, create an extract_from_seatv helper and try that
        return extract_from_seatv(html_content)
        
    except Exception as e:
        logger.error(f"Error in specialized SeaTV extraction: {str(e)}")
        logger.error(traceback.format_exc())
        return {'success': False, 'error': f"Failed to extract Dailymotion link from SeaTV: {str(e)}"}

def extract_without_browser(url):
    """Extract Dailymotion links without using a browser"""
    logger.info(f"Extracting from {url} without browser")
    
    html_content = fetch_url_content(url)
    if not html_content:
        return {'success': False, 'error': "Failed to fetch page content"}
    
    # Extract Dailymotion URLs from page source
    dailymotion_links = extract_dailymotion_from_source(html_content)
    
    if dailymotion_links:
        logger.info(f"Found Dailymotion link in page source: {dailymotion_links[0]}")
        return {'success': True, 'link': dailymotion_links[0]}
    
    # Special handling for specific sites
    if 'seatv-24' in url or 'perfect-world' in url:
        logger.info("Detected SeaTV or Perfect World site, applying specialized extraction")
        return extract_from_seatv(html_content)
    
    # Specific handling for Lucifer Donghua site
    if 'luciferdonghua' in url:
        logger.info("Detected Lucifer Donghua site, applying specialized extraction")
        return extract_from_lucifer_direct(url, html_content)
    
    # If not found directly, check for server selection elements in the HTML
    # and try to identify which part of the page might contain the video
    try:
        # Look for common patterns that indicate server selection
        server_patterns = [
            r'<div[^>]*class="[^"]*server[^"]*"[^>]*>(.*?)</div>',
            r'<ul[^>]*class="[^"]*servers[^"]*"[^>]*>(.*?)</ul>',
            r'<div[^>]*id="[^"]*player[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*player-container[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*video-player[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern in server_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            for match in matches:
                # Check if this section contains "daily" or "dailymotion"
                if 'daily' in match.lower():
                    # Extract URLs from this section
                    dailymotion_links = extract_dailymotion_from_source(match)
                    if dailymotion_links:
                        return {'success': True, 'link': dailymotion_links[0]}
    except Exception as e:
        logger.error(f"Error in advanced non-browser extraction: {str(e)}")
    
    # Try to find any iframe that might be a video player
    iframe_pattern = r'<iframe[^>]*src="([^"]*)"[^>]*>'
    iframes = re.findall(iframe_pattern, html_content)
    for iframe_src in iframes:
        logger.info(f"Found iframe with src: {iframe_src}")
        if 'dailymotion' in iframe_src or 'dai.ly' in iframe_src:
            return {'success': True, 'link': clean_dailymotion_url(iframe_src)}
        elif iframe_src.startswith('//'):
            # Handle protocol-relative URLs
            full_url = f"https:{iframe_src}"
            if 'dailymotion' in full_url or 'dai.ly' in full_url:
                return {'success': True, 'link': clean_dailymotion_url(full_url)}
        
        # If iframe src is not a Dailymotion link directly, try to load that page
        # and check if it contains Dailymotion content
        if iframe_src.startswith('http'):
            iframe_content = fetch_url_content(iframe_src)
            if iframe_content:
                iframe_dailymotion_links = extract_dailymotion_from_source(iframe_content)
                if iframe_dailymotion_links:
                    return {'success': True, 'link': iframe_dailymotion_links[0]}
    
    return {'success': False, 'error': "No Dailymotion content found on this page"}

def extract_from_seatv(html_content):
    """Special extraction for SeaTV and similar sites"""
    logger.info("Using specialized extraction for SeaTV/Perfect World sites")
    
    # These sites often have a specific pattern for including video players
    try:
        # Look for player containers
        player_patterns = [
            r'<div[^>]*id="player-container"[^>]*>(.*?)</div>',
            r'<div[^>]*class="player-embed"[^>]*>(.*?)</div>',
            r'<div[^>]*id="video-player"[^>]*>(.*?)</div>',
            r'<div[^>]*class="embed-responsive"[^>]*>(.*?)</div>'
        ]
        
        for pattern in player_patterns:
            player_sections = re.findall(pattern, html_content, re.DOTALL)
            for section in player_sections:
                dailymotion_links = extract_dailymotion_from_source(section)
                if dailymotion_links:
                    return {'success': True, 'link': dailymotion_links[0]}
        
        # Look for data attributes that might contain video information
        data_patterns = [
            r'data-src="([^"]*dailymotion[^"]*)"',
            r'data-video="([^"]*dailymotion[^"]*)"',
            r'data-player-src="([^"]*dailymotion[^"]*)"'
        ]
        
        for pattern in data_patterns:
            data_matches = re.findall(pattern, html_content)
            for match in data_matches:
                return {'success': True, 'link': clean_dailymotion_url(match)}
        
        # Look for scripts that might contain video source information
        script_sections = re.findall(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL)
        for script in script_sections:
            if 'dailymotion' in script.lower() or 'dai.ly' in script.lower():
                # Look for URL patterns within scripts
                dailymotion_links = extract_dailymotion_from_source(script)
                if dailymotion_links:
                    return {'success': True, 'link': dailymotion_links[0]}
                
                # Look for specific script patterns used by these sites
                video_id_match = re.search(r'["\']video["\']:\s*["\']([a-zA-Z0-9]+)["\']', script)
                if video_id_match:
                    video_id = video_id_match.group(1)
                    return {'success': True, 'link': f"https://www.dailymotion.com/video/{video_id}"}
        
        # Check for server tabs that might contain Dailymotion options
        server_tabs = re.findall(r'<a[^>]*class="[^"]*server-tab[^"]*"[^>]*>(.*?)</a>', html_content, re.DOTALL)
        for tab in server_tabs:
            if 'daily' in tab.lower():
                # Find associated content
                tab_id_match = re.search(r'data-tab="([^"]*)"', tab)
                if tab_id_match:
                    tab_id = tab_id_match.group(1)
                    tab_content = re.findall(f'<div[^>]*data-tab-content="{tab_id}"[^>]*>(.*?)</div>', html_content, re.DOTALL)
                    for content in tab_content:
                        dailymotion_links = extract_dailymotion_from_source(content)
                        if dailymotion_links:
                            return {'success': True, 'link': dailymotion_links[0]}
        
    except Exception as e:
        logger.error(f"Error in SeaTV specialized extraction: {str(e)}")
    
    # Generic iframe search as a fallback
    iframe_pattern = r'<iframe[^>]*src="([^"]*)"[^>]*>'
    iframes = re.findall(iframe_pattern, html_content)
    for iframe_src in iframes:
        if iframe_src and iframe_src.strip():
            logger.info(f"Found iframe in SeaTV: {iframe_src}")
            # For SeaTV sites, even if the iframe is not directly from Dailymotion,
            # it could be a proxy or redirect to Dailymotion
            try:
                iframe_content = fetch_url_content(iframe_src)
                if iframe_content:
                    dailymotion_links = extract_dailymotion_from_source(iframe_content)
                    if dailymotion_links:
                        return {'success': True, 'link': dailymotion_links[0]}
            except:
                # If direct fetch fails, just return the iframe src for manual checking
                return {'success': True, 'link': iframe_src, 'note': 'This might be an indirect link - open manually if needed'}
    
    return {'success': False, 'error': "No Dailymotion content found on this SeaTV page"}

def extract_from_lucifer(driver, url):
    """Extract Dailymotion link from Lucifer website"""
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Loading Lucifer URL (attempt {attempt+1}): {url}")
            driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Look for server selection element
            server_buttons = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".server-item, .server-button, [data-server]"))
            )
            
            # Click on Dailymotion server
            dailymotion_button = None
            for button in server_buttons:
                if 'daily' in button.text.lower() or 'dailymotion' in button.text.lower():
                    dailymotion_button = button
                    break
            
            if not dailymotion_button:
                logger.warning("Dailymotion server option not found, checking iframe directly")
                return extract_dailymotion_iframe(driver)
            
            logger.info("Clicking Dailymotion server option")
            dailymotion_button.click()
            time.sleep(2)
            
            # Extract iframe after server selection
            return extract_dailymotion_iframe(driver)
        
        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                return {'success': False, 'error': f"Timeout while processing Lucifer website: {str(e)}"}
            time.sleep(2)  # Wait before retrying

def extract_from_wetv(driver, url):
    """Extract Dailymotion link from We TV website"""
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Loading We TV URL (attempt {attempt+1}): {url}")
            driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # We TV might have different server selection UI
            server_selectors = [
                ".server-list .server", 
                ".server-container [data-server]",
                ".video-servers .server-item",
                "a[href*='server']",
                "button[data-server]"
            ]
            
            for selector in server_selectors:
                try:
                    server_buttons = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    
                    # Click on Dailymotion server
                    for button in server_buttons:
                        if 'daily' in button.text.lower() or 'dailymotion' in button.text.lower():
                            logger.info("Found Dailymotion server option, clicking")
                            button.click()
                            time.sleep(2)
                            return extract_dailymotion_iframe(driver)
                except:
                    continue
            
            # If we couldn't find or click a server option, try extracting iframe directly
            logger.warning("Could not find server options, trying direct iframe extraction")
            return extract_dailymotion_iframe(driver)
            
        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                return {'success': False, 'error': f"Timeout while processing We TV website: {str(e)}"}
            time.sleep(2)  # Wait before retrying

def extract_generic(driver, url):
    """Generic extraction method for websites not specifically supported"""
    try:
        logger.info(f"Attempting generic extraction from: {url}")
        driver.get(url)
        time.sleep(3)
        
        # Try to find and click on any element that might be a server selection for Dailymotion
        server_selectors = [
            "*[class*='server']", 
            "*[id*='server']",
            "a[href*='daily']", 
            "button:contains('Daily')",
            "*[data-server*='daily']"
        ]
        
        for selector in server_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if 'daily' in element.text.lower():
                        logger.info("Found potential Dailymotion server option, clicking")
                        element.click()
                        time.sleep(2)
                        break
            except:
                continue
        
        # After clicking (or not finding) server options, try to extract the iframe
        return extract_dailymotion_iframe(driver)
    
    except Exception as e:
        logger.error(f"Generic extraction failed: {str(e)}")
        return {'success': False, 'error': f"Failed to extract from unknown website format: {str(e)}"}

def extract_dailymotion_iframe(driver):
    """Extract Dailymotion link from iframe on the page"""
    try:
        # Find iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        logger.info(f"Found {len(iframes)} iframes on the page")
        
        # Check each iframe for Dailymotion content
        for iframe in iframes:
            src = iframe.get_attribute("src")
            if src and ('dailymotion.com' in src or 'dai.ly' in src):
                logger.info(f"Found Dailymotion iframe: {src}")
                return {'success': True, 'link': clean_dailymotion_url(src)}
        
        # If no Dailymotion iframe found, check page source for Dailymotion links
        page_source = driver.page_source
        dailymotion_links = extract_dailymotion_from_source(page_source)
        
        if dailymotion_links:
            logger.info(f"Found Dailymotion link in page source: {dailymotion_links[0]}")
            return {'success': True, 'link': dailymotion_links[0]}
        
        return {'success': False, 'error': "No Dailymotion content found on this page"}
    
    except Exception as e:
        logger.error(f"Error extracting from iframe: {str(e)}")
        return {'success': False, 'error': f"Failed to extract Dailymotion link: {str(e)}"}

def extract_dailymotion_from_source(html_source):
    """Extract Dailymotion URLs from page source using regex"""
    if not html_source:
        return []
        
    # Patterns to look for Dailymotion links
    direct_url_patterns = [
        r'https?://(?:www\.)?dailymotion\.com/(?:embed/)?video/([a-zA-Z0-9]+)',
        r'https?://(?:www\.)?dai\.ly/([a-zA-Z0-9]+)',
        r'//(?:www\.)?dailymotion\.com/(?:embed/)?video/([a-zA-Z0-9]+)',
        r'//(?:www\.)?dai\.ly/([a-zA-Z0-9]+)'
    ]
    
    attribute_url_patterns = [
        r'data-src="(https?://(?:www\.)?dailymotion\.com/(?:embed/)?video/[a-zA-Z0-9]+)"',
        r'src="(https?://(?:www\.)?dailymotion\.com/(?:embed/)?video/[a-zA-Z0-9]+)"',
        r'data-src="(//(?:www\.)?dailymotion\.com/(?:embed/)?video/[a-zA-Z0-9]+)"',
        r'src="(//(?:www\.)?dailymotion\.com/(?:embed/)?video/[a-zA-Z0-9]+)"',
        r'data-player="(https?://(?:www\.)?dailymotion\.com/(?:embed/)?video/[a-zA-Z0-9]+)"',
        r'data-video-url="(https?://(?:www\.)?dailymotion\.com/(?:embed/)?video/[a-zA-Z0-9]+)"'
    ]
    
    # Patterns for javascript-embedded video IDs
    script_patterns = [
        r'dailymotion\.com/embed/video/([a-zA-Z0-9]+)',
        r'dai\.ly/([a-zA-Z0-9]+)',
        r'["\'](?:video_id|videoId|video)["\']:\s*["\']([a-zA-Z0-9]+)["\']',
        r'DM\.player\([^,]+,\s*["\']([a-zA-Z0-9]+)["\']'
    ]
    
    results = []
    
    # Extract direct URLs
    for pattern in direct_url_patterns:
        matches = re.findall(pattern, html_source)
        for match in matches:
            if match and len(match) > 5:  # Most Dailymotion IDs are 6+ chars
                results.append(f"https://dailymotion.com/video/{match}")
    
    # Extract from HTML attributes
    for pattern in attribute_url_patterns:
        matches = re.findall(pattern, html_source)
        for match in matches:
            if match:
                if match.startswith('//'):
                    results.append(clean_dailymotion_url(f"https:{match}"))
                else:
                    results.append(clean_dailymotion_url(match))
    
    # Extract from JavaScript
    for pattern in script_patterns:
        matches = re.findall(pattern, html_source)
        for match in matches:
            if match and len(match) > 5:  # Most Dailymotion IDs are 6+ chars
                results.append(f"https://dailymotion.com/video/{match}")
    
    # Remove duplicates while preserving order
    unique_results = []
    for result in results:
        if result not in unique_results:
            unique_results.append(result)
    
    return unique_results

def clean_dailymotion_url(url):
    """Clean up and normalize Dailymotion URL to standard video format"""
    # Extract video ID
    video_id = None
    
    # Handle dai.ly short links
    if 'dai.ly' in url:
        match = re.search(r'dai\.ly/([a-zA-Z0-9]+)', url)
        if match:
            video_id = match.group(1)
    
    # Handle geo.dailymotion.com player links
    elif 'geo.dailymotion.com/player' in url:
        # Extract from format like: geo.dailymotion.com/player/xkyen.html?video=k1ugc7WgEsx3ZqCY132
        match = re.search(r'[?&]video=([a-zA-Z0-9]+)', url)
        if match:
            video_id = match.group(1)
    
    # Handle dailymotion.com iframe embed links
    elif 'dailymotion.com/embed' in url:
        match = re.search(r'dailymotion\.com/embed/video/([a-zA-Z0-9]+)', url)
        if match:
            video_id = match.group(1)
    
    # Handle regular dailymotion.com links
    elif 'dailymotion.com' in url:
        match = re.search(r'dailymotion\.com/(?:embed/)?video/([a-zA-Z0-9]+)', url)
        if match:
            video_id = match.group(1)
    
    if video_id:
        # Return a clean, standard Dailymotion URL (without www prefix as per user request)
        return f"https://dailymotion.com/video/{video_id}"
    
    # If we couldn't extract a video ID, return the original URL
    return url
