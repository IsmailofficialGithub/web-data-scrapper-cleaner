"""
Selenium Web Scraper
Takes a website URL and saves its HTML content to a text file.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import sys
import os
from datetime import datetime


def setup_driver(headless=True, stealth_mode=True):
    """
    Setup and configure Chrome WebDriver with anti-detection features.
    
    Args:
        headless (bool): Run browser in headless mode (background)
        stealth_mode (bool): Enable stealth mode to avoid bot detection
    
    Returns:
        webdriver.Chrome: Configured Chrome driver
    """
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless=new')  # Use new headless mode
    
    # Basic options
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Anti-detection options
    if stealth_mode:
        # Remove automation indicators
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Make browser look more realistic
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins-discovery')
        chrome_options.add_argument('--start-maximized')
    
    # Realistic user agent (updated Chrome version)
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    # Additional headers
    chrome_options.add_argument('--lang=en-US,en')
    chrome_options.add_argument('--accept-lang=en-US,en')
    
    try:
        # Use webdriver-manager to automatically handle ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute stealth scripts to hide webdriver properties
        if stealth_mode:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    window.chrome = {
                        runtime: {}
                    };
                '''
            })
        
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("\nMake sure you have Google Chrome installed.")
        print("ChromeDriver will be automatically downloaded by webdriver-manager.")
        # sys.exit(1)


def detect_error_page(html_content, url):
    """
    Detect if the page is an error page (403, 404, 500, etc.)
    
    Args:
        html_content (str): HTML content to check
        url (str): URL that was scraped
    
    Returns:
        tuple: (is_error, error_type, error_message) or (False, None, None)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check title for common error patterns
    title = soup.find('title')
    title_text = title.get_text().lower() if title else ''
    
    # Check body text for error messages
    body_text = soup.get_text().lower()
    
    # Common error patterns
    error_patterns = {
        '403': ['403', 'forbidden', 'access denied'],
        '404': ['404', 'not found', 'page not found', 'does not exist'],
        '500': ['500', 'internal server error', 'server error'],
        '401': ['401', 'unauthorized', 'authentication required'],
        '503': ['503', 'service unavailable', 'temporarily unavailable']
    }
    
    for error_code, patterns in error_patterns.items():
        # Check title
        if any(pattern in title_text for pattern in patterns):
            return True, error_code, f"Error {error_code} detected in page title"
        
        # Check if error code appears prominently in body
        if error_code in body_text:
            # Count occurrences - if it appears multiple times, likely an error page
            count = body_text.count(error_code)
            if count >= 2:
                return True, error_code, f"Error {error_code} detected in page content"
    
    return False, None, None


def extract_links(html_content, base_url):
    """
    Extract all href links from <a> tags in HTML content.
    
    Args:
        html_content (str): HTML content to parse
        base_url (str): Base URL for resolving relative links
    
    Returns:
        set: Set of absolute URLs found in <a> tags
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    
    # Find all <a> tags with href attributes
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        
        # Skip empty, javascript, mailto, tel, and anchor links
        if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#', 'data:')):
            continue
        
        # Convert relative URLs to absolute
        absolute_url = urljoin(base_url, href)
        
        # Parse URL to validate and normalize
        parsed = urlparse(absolute_url)
        if parsed.scheme in ('http', 'https') and parsed.netloc:
            links.add(absolute_url)
    
    return links


def get_safe_filename(url, base_dir=None):
    """
    Generate a safe filename from URL.
    
    Args:
        url (str): URL to convert to filename
        base_dir (str, optional): Base directory for the file
    
    Returns:
        str: Safe filename path
    """
    parsed = urlparse(url)
    domain = parsed.netloc.replace('.', '_').replace(':', '_')
    path = parsed.path.strip('/').replace('/', '_').replace('?', '_').replace('&', '_')
    
    if not path or path == '_':
        path = 'index'
    
    # Limit filename length
    if len(path) > 100:
        path = path[:100]
    
    filename = f"{domain}_{path}"
    # Remove invalid filename characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    
    if base_dir:
        return os.path.join(base_dir, filename + '.html')
    return filename + '.html'


def scrape_website(url, output_file=None, wait_time=5, extract_links_flag=False, base_output_dir=None, headless=True, stealth_mode=True, add_delay=False):
    """
    Scrape HTML content from a website URL and save to text file.
    
    Args:
        url (str): The website URL to scrape
        output_file (str, optional): Output file path. If None, generates automatically.
        wait_time (int): Time to wait for page to load (seconds)
        extract_links_flag (bool): Whether to extract and scrape links from the page
        base_output_dir (str, optional): Base directory for organizing scraped files
        headless (bool): Run browser in headless mode
        stealth_mode (bool): Enable stealth mode to avoid bot detection
        add_delay (bool): Add random delay before loading page (helps avoid rate limiting)
    
    Returns:
        tuple: (output_file, list of links found) or (None, []) if error
    """
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    print(f"\n{'='*60}")
    print(f"Scraping URL: {url}")
    print(f"{'='*60}")
    
    driver = None
    try:
        # Add random delay if requested (helps avoid rate limiting)
        if add_delay:
            import time
            import random
            delay = random.uniform(1, 3)
            print(f"Adding {delay:.1f}s delay to appear more human-like...")
            time.sleep(delay)
        
        driver = setup_driver(headless=headless, stealth_mode=stealth_mode)
        
        # Set additional headers to appear more like a real browser
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            "acceptLanguage": "en-US,en;q=0.9"
        })
        
        # Navigate to URL
        print("Loading page...")
        driver.get(url)
        
        # Wait for page to load
        print(f"Waiting {wait_time} seconds for page to load...")
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get the HTML content
        html_content = driver.page_source
        
        # Check for error pages
        is_error, error_type, error_msg = detect_error_page(html_content, url)
        if is_error:
            print(f"⚠ WARNING: {error_msg}")
            print(f"⚠ This appears to be an error page ({error_type}), not the actual content")
            print(f"⚠ The page may have blocked access or the URL may be invalid")
        
        # Extract links if requested
        links = set()
        if extract_links_flag:
            print("Extracting links from page...")
            links = extract_links(html_content, url)
            print(f"Found {len(links)} unique links")
        
        # Determine output directory structure
        if base_output_dir:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('.', '_').replace(':', '_')
            domain_folder = os.path.join(base_output_dir, domain)
            if not os.path.exists(domain_folder):
                os.makedirs(domain_folder)
            html_folder = os.path.join(domain_folder, 'html')
            cleaned_folder = os.path.join(domain_folder, 'cleaned')
            if not os.path.exists(html_folder):
                os.makedirs(html_folder)
            if not os.path.exists(cleaned_folder):
                os.makedirs(cleaned_folder)
        else:
            html_folder = '.'
            cleaned_folder = '.'
        
        # Generate output filename if not provided
        if output_file is None:
            output_file = get_safe_filename(url, html_folder)
        else:
            # If output_file provided but base_output_dir exists, put it in html folder
            if base_output_dir:
                output_file = os.path.join(html_folder, os.path.basename(output_file))
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else '.'
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save HTML to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ HTML content saved to: {output_file}")
        print(f"✓ File size: {len(html_content)} characters")
        
        return output_file, list(links)
        
    except Exception as e:
        print(f"Error scraping website: {e}")
        import traceback
        traceback.print_exc()
        return None, []
        
    finally:
        if driver:
            driver.quit()


def clean_html_data(input_file, output_file=None, cleaned_folder=None):
    """
    Clean HTML file and extract text content from all nodes.
    
    Args:
        input_file (str): Path to the HTML file to clean
        output_file (str, optional): Output file path. If None, generates automatically.
        cleaned_folder (str, optional): Folder to save cleaned files. If None, uses same dir as input.
    
    Returns:
        str: Path to the output file, or None if error
    """
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found!")
        return None
    
    print(f"Cleaning HTML file: {os.path.basename(input_file)}")
    
    try:
        # Read HTML file
        with open(input_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(["script", "style", "meta", "link", "noscript", "head"]):
            element.decompose()
        
        # Get text from all nodes
        text_content = soup.get_text()
        
        # Clean the text
        # Split into lines
        lines = text_content.split('\n')
        # Remove empty lines and strip whitespace
        cleaned_lines = []
        for line in lines:
            cleaned_line = line.strip()
            # Remove lines that are too short or only whitespace
            if cleaned_line and len(cleaned_line) > 1:
                cleaned_lines.append(cleaned_line)
        
        # Join lines with newlines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove excessive blank lines (more than 2 consecutive newlines)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        # Generate output filename if not provided
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = f"{base_name}_cleaned.txt"
        
        # Use cleaned_folder if provided
        if cleaned_folder:
            output_file = os.path.join(cleaned_folder, os.path.basename(output_file))
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else '.'
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save cleaned text to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        print(f"  ✓ Cleaned text saved to: {os.path.basename(output_file)}")
        
        return output_file
        
    except Exception as e:
        print(f"  ✗ Error cleaning HTML file: {e}")
        return None


def scrape_with_links(url, max_links=None, wait_time=5, base_output_dir=None, headless=True, stealth_mode=True, add_delay=False):
    """
    Scrape a website and all links found on it, then clean all files.
    
    Args:
        url (str): Starting URL to scrape
        max_links (int, optional): Maximum number of links to scrape. If None, scrapes all.
        wait_time (int): Time to wait for each page to load (seconds)
        base_output_dir (str, optional): Base directory for organizing files
        headless (bool): Run browser in headless mode
        stealth_mode (bool): Enable stealth mode to avoid bot detection
        add_delay (bool): Add random delays between requests
    
    Returns:
        dict: Summary of scraping results
    """
    # Create base output directory
    if base_output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_output_dir = f"scraped_data_{timestamp}"
    
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)
    
    print(f"\n{'='*60}")
    print(f"Starting comprehensive scrape")
    print(f"Output directory: {base_output_dir}")
    print(f"{'='*60}\n")
    
    # Scrape initial URL
    initial_file, links = scrape_website(url, extract_links_flag=True, 
                                         wait_time=wait_time, base_output_dir=base_output_dir,
                                         headless=headless, stealth_mode=stealth_mode, add_delay=add_delay)
    
    if not initial_file:
        print("Failed to scrape initial URL!")
        return None
    
    # Clean initial file
    parsed = urlparse(url)
    domain = parsed.netloc.replace('.', '_').replace(':', '_')
    domain_folder = os.path.join(base_output_dir, domain)
    cleaned_folder = os.path.join(domain_folder, 'cleaned')
    clean_html_data(initial_file, cleaned_folder=cleaned_folder)
    
    scraped_files = [initial_file]
    scraped_urls = {url}
    
    # Limit number of links to scrape
    if max_links:
        links = list(links)[:max_links]
    
    print(f"\n{'='*60}")
    print(f"Scraping {len(links)} additional links...")
    print(f"{'='*60}\n")
    
    # Scrape each link
    driver = None
    try:
        driver = setup_driver(headless=headless, stealth_mode=stealth_mode)
        
        # Set user agent
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            "acceptLanguage": "en-US,en;q=0.9"
        })
        
        for i, link_url in enumerate(links, 1):
            if link_url in scraped_urls:
                continue
            
            print(f"\n[{i}/{len(links)}] Processing: {link_url}")
            
            # Add delay between requests if requested
            if add_delay and i > 1:
                import time
                import random
                delay = random.uniform(2, 5)
                print(f"  Waiting {delay:.1f}s before next request...")
                time.sleep(delay)
            
            try:
                driver.get(link_url)
                WebDriverWait(driver, wait_time).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                html_content = driver.page_source
                
                # Check for error pages
                is_error, error_type, error_msg = detect_error_page(html_content, link_url)
                if is_error:
                    print(f"  ⚠ WARNING: {error_msg} - Skipping link extraction")
                    # Still save the error page but don't extract links from it
                
                # Determine folder structure
                parsed_link = urlparse(link_url)
                link_domain = parsed_link.netloc.replace('.', '_').replace(':', '_')
                link_domain_folder = os.path.join(base_output_dir, link_domain)
                link_html_folder = os.path.join(link_domain_folder, 'html')
                link_cleaned_folder = os.path.join(link_domain_folder, 'cleaned')
                
                if not os.path.exists(link_html_folder):
                    os.makedirs(link_html_folder)
                if not os.path.exists(link_cleaned_folder):
                    os.makedirs(link_cleaned_folder)
                
                # Save HTML file
                html_file = get_safe_filename(link_url, link_html_folder)
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                if is_error:
                    print(f"  ⚠ Saved (ERROR PAGE): {os.path.basename(html_file)}")
                else:
                    print(f"  ✓ Saved: {os.path.basename(html_file)}")
                
                # Clean the file (even if it's an error page, for reference)
                clean_html_data(html_file, cleaned_folder=link_cleaned_folder)
                
                scraped_files.append(html_file)
                scraped_urls.add(link_url)
                
            except Exception as e:
                print(f"  ✗ Error scraping {link_url}: {e}")
                continue
        
    finally:
        if driver:
            driver.quit()
    
    print(f"\n{'='*60}")
    print(f"Scraping Complete!")
    print(f"{'='*60}")
    print(f"Total URLs scraped: {len(scraped_files)}")
    print(f"Output directory: {base_output_dir}")
    print(f"\nFiles organized by domain:")
    print(f"  - html/    : Raw HTML files")
    print(f"  - cleaned/  : Cleaned text files")
    
    return {
        'base_dir': base_output_dir,
        'files': scraped_files,
        'urls': list(scraped_urls)
    }


def main():
    """Main function to handle command line arguments or interactive mode"""
    if len(sys.argv) < 2:
        # Interactive mode
        print("=" * 60)
        print("Web Scraper - Interactive Mode")
        print("=" * 60)
        print()
        
        url = input("Enter website URL: ").strip()
        if not url:
            print("Error: URL cannot be empty!")
            # sys.exit(1)
        
        print("\nOptions:")
        print("1. Scrape only this URL")
        print("2. Scrape this URL + all links found on it")
        choice = input("Choose option (1 or 2): ").strip()
        
        # Anti-detection options
        print("\nAnti-detection options (to bypass 403 errors):")
        headless_input = input("Run in headless mode? (y/n, default=y): ").strip().lower()
        headless = headless_input != 'n'
        
        stealth_input = input("Enable stealth mode? (y/n, default=y): ").strip().lower()
        stealth_mode = stealth_input != 'n'
        
        delay_input = input("Add delays between requests? (y/n, default=n): ").strip().lower()
        add_delay = delay_input == 'y'
        
        if choice == '2':
            max_links_input = input("Max links to scrape (press Enter for all): ").strip()
            max_links = int(max_links_input) if max_links_input else None
            output_dir = input("Output directory (press Enter for auto-generated): ").strip()
            output_dir = output_dir if output_dir else None
            
            print()
            scrape_with_links(url, max_links=max_links, base_output_dir=output_dir,
                            headless=headless, stealth_mode=stealth_mode, add_delay=add_delay)
        else:
            output_file = input("Enter output filename (press Enter for auto-generated): ").strip()
            if not output_file:
                output_file = None
            print()
            scrape_website(url, output_file, headless=headless, stealth_mode=stealth_mode, add_delay=add_delay)
    else:
        # Command line mode
        url = sys.argv[1]
        
        # Parse flags
        headless = '--no-headless' not in sys.argv
        stealth_mode = '--no-stealth' not in sys.argv
        add_delay = '--delay' in sys.argv or '-d' in sys.argv
        
        # Check for --links flag
        if '--links' in sys.argv or '-l' in sys.argv:
            max_links = None
            if '--max' in sys.argv:
                idx = sys.argv.index('--max')
                if idx + 1 < len(sys.argv):
                    max_links = int(sys.argv[idx + 1])
            
            output_dir = None
            if '--output' in sys.argv or '-o' in sys.argv:
                flag = '--output' if '--output' in sys.argv else '-o'
                idx = sys.argv.index(flag)
                if idx + 1 < len(sys.argv):
                    output_dir = sys.argv[idx + 1]
            
            scrape_with_links(url, max_links=max_links, base_output_dir=output_dir,
                            headless=headless, stealth_mode=stealth_mode, add_delay=add_delay)
        else:
            output_file = sys.argv[2] if len(sys.argv) > 2 else None
            scrape_website(url, output_file, headless=headless, stealth_mode=stealth_mode, add_delay=add_delay)


if __name__ == "__main__":
    main()
