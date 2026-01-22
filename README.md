# Web Data Scraper & Cleaner

A Selenium-based web scraper that takes a website URL and saves its HTML content to a text file, plus an HTML cleaner that extracts clean text from HTML files.

## Features

### Web Scraper
- Fetches HTML content from any website URL
- Saves HTML to a text file
- Automatic filename generation with timestamp
- Headless browser mode (runs in background)
- Custom output file support

### HTML Cleaner
- Extracts text content from HTML files
- Removes scripts, styles, and metadata
- Cleans and formats text output
- Removes empty lines and excessive whitespace
- Saves cleaned text to a new txt file

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. ChromeDriver will be automatically managed by webdriver-manager, or you can install ChromeDriver manually:
   - Download from [ChromeDriver Downloads](https://chromedriver.chromium.org/)
   - Make sure you have Google Chrome installed

## Quick Start

### Auto-Run (Windows)

#### Web Scraper
1. **Double-click `run_scraper.bat`** - Opens interactive mode where you can enter URL
2. **Double-click `run_scraper_auto.bat`** - Auto-runs with a pre-configured URL (edit the file to change URL)
3. **Double-click `run_scraper_with_links.bat`** - Auto-runs and scrapes all links found on the page

#### HTML Cleaner
1. **Double-click `run_cleaner.bat`** - Opens interactive mode to clean HTML files
2. **Double-click `run_cleaner_auto.bat`** - Auto-runs with the `data` file (edit the file to change input)

#### Installation
- **Double-click `install.bat`** - Installs all dependencies automatically

### Command Line Usage

#### Interactive Mode (No arguments)
```bash
python scraper.py
```
This will prompt you to enter the URL and output filename.

#### Basic Usage
```bash
python scraper.py <website_url>
```

#### With Custom Output File
```bash
python scraper.py <website_url> <output_file.txt>
```

#### Examples
```bash
# Interactive mode (prompts for input)
python scraper.py

# Scrape example.com (auto-generates filename)
python scraper.py https://example.com

# Scrape and save to specific file
python scraper.py https://example.com output.html

# Scrape without https:// prefix (automatically adds it)
python scraper.py example.com

# Scrape URL and all links found on it (organized in folders)
python scraper.py https://example.com --links

# Scrape with max links limit
python scraper.py https://example.com --links --max 10

# Scrape with custom output directory
python scraper.py https://example.com --links --output my_scraped_data

# Bypass 403 errors - use visible browser (recommended for protected sites)
python scraper.py https://example.com --no-headless

# Add delays between requests to avoid rate limiting
python scraper.py https://example.com --delay

# Combine options for maximum success
python scraper.py https://example.com --no-headless --delay
```

### HTML Cleaner Usage

#### Interactive Mode (No arguments)
```bash
python cleaner.py
```
This will prompt you to enter the HTML file path and output filename.

#### Basic Usage
```bash
python cleaner.py <html_file>
```

#### With Custom Output File
```bash
python cleaner.py <html_file> <output_file.txt>
```

#### Examples
```bash
# Interactive mode (prompts for input)
python cleaner.py

# Clean data file (auto-generates filename)
python cleaner.py data

# Clean and save to specific file
python cleaner.py data cleaned_output.txt
```

## How It Works

### Web Scraper
1. The script uses Selenium with Chrome WebDriver
2. Opens the URL in a headless browser
3. Waits for the page to fully load
4. Extracts the HTML content
5. Saves it to a text file

### Link Scraping Mode (--links)
When using `--links` flag:
1. Scrapes the initial URL
2. Extracts all `<a>` tag href links from the page
3. Scrapes each found link
4. Organizes files by domain in folders:
   - `domain_name/html/` - Raw HTML files
   - `domain_name/cleaned/` - Cleaned text files
5. Automatically cleans all scraped HTML files

### HTML Cleaner
1. Reads the HTML file
2. Parses HTML with BeautifulSoup
3. Removes scripts, styles, meta tags, and other non-content elements
4. Extracts text from all remaining nodes
5. Cleans text by removing empty lines and excessive whitespace
6. Saves cleaned text to a new txt file

## Output

### Web Scraper
- If no output file is specified, the script generates a filename based on the domain and timestamp
- Format: `domain_timestamp.txt` (e.g., `example_com_20231215_143022.txt`)
- Files are saved in the current directory by default

### Link Scraping Mode
- Creates a base output directory (auto-generated or custom)
- Organizes files by domain:
  ```
  scraped_data_20231215_143022/
    domain1_com/
      html/
        domain1_com_index.html
        domain1_com_page1.html
      cleaned/
        domain1_com_index_cleaned.txt
        domain1_com_page1_cleaned.txt
    domain2_com/
      html/
        ...
      cleaned/
        ...
  ```

### HTML Cleaner
- If no output file is specified, generates: `filename_cleaned_timestamp.txt`
- Removes all HTML tags and extracts only text content
- Preserves line structure and removes excessive blank lines

## Bypassing 403 Errors

If you encounter 403 Forbidden errors, the scraper includes anti-detection features:

- **Stealth Mode** (enabled by default): Hides automation indicators
- **Non-Headless Mode**: Use `--no-headless` to run with visible browser (more effective)
- **Delays**: Use `--delay` to add random delays between requests

See `BYPASS_403_GUIDE.md` for detailed instructions on bypassing protected sites.

## Requirements

- Python 3.7+
- Google Chrome browser (for scraper)
- Selenium (for web scraping)
- webdriver-manager (for automatic ChromeDriver management)
- beautifulsoup4 (for HTML parsing and cleaning)
- lxml (HTML parser backend)