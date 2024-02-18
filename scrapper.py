from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from PIL import Image
import io
import time
from bs4 import BeautifulSoup
from PyPDF2 import PdfMerger
import urllib.parse

def extract_internal_links(url, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        parsed_href = urllib.parse.urlparse(href)
        if parsed_href.netloc == '' or parsed_href.netloc == urllib.parse.urlparse(url).netloc:
            defragged_href, _ = urllib.parse.urldefrag(href)
            full_url = urllib.parse.urljoin(url, defragged_href)
            links.add(full_url)
    return links

def capture_page_to_pdf(driver, url):
    try:
        driver.get(url)
        print(f"Capturing page: {url}")
        time.sleep(2)

        total_width = driver.execute_script("return document.body.offsetWidth")
        total_height = driver.execute_script("return document.body.parentNode.scrollHeight")

        view_height = 800
        driver.set_window_size(total_width, view_height)
        time.sleep(2)

        scrolls = total_height // view_height
        pdf_pages = []

        for i in range(scrolls + 1):
            driver.execute_script(f"window.scrollTo(0, {min((i * view_height) - 150, total_height)});")
            time.sleep(2)

            screenshot = driver.get_screenshot_as_png()
            image = Image.open(io.BytesIO(screenshot))
            pdf_bytes = io.BytesIO()
            image.convert('RGB').save(pdf_bytes, format='PDF')
            pdf_pages.append(pdf_bytes.getvalue())
            print(f"Captured {i+1}/{scrolls+1} pages")

        return pdf_pages
    except Exception as e:
        print(f"Error capturing page {url}: {e}")
        return None

def handle_mailto_link(url, driver, pdf_merger):
    print(f"Skipping page {url} because it contains a 'mailto:' link.")
    return

def dfs(url, driver, visited, pdf_merger):
    if url in visited:
        return
    visited.add(url)
    try:
        driver.get(url)
    except (WebDriverException, TimeoutException) as e:
        print(f"Error accessing {url}: {e}")
        return
    except Exception as e:
        print(f"Unexpected error accessing {url}: {e}")
        return

    page_content = driver.page_source
    pdf_pages = capture_page_to_pdf(driver, url)
    if pdf_pages:
        for page in pdf_pages:
            pdf_merger.append(io.BytesIO(page))
        # return
    
    for link in extract_internal_links(url, page_content):
        dfs(link, driver, visited, pdf_merger)

def main(start_url):
    if not start_url.startswith('http'):
        start_url = 'https://' + start_url
    visited = set()
    pdf_merger = PdfMerger()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    try:
        driver = webdriver.Chrome(options)
        dfs(start_url, driver, visited, pdf_merger)
    except WebDriverException as e:
        print(f"WebDriver error: {e}")
    except Exception as e:
        print(f"An error occurred during execution: {e}")
    finally:
        if 'driver' in locals() and driver is not None:
            driver.quit()
        with open('output.pdf', 'wb') as f:
            pdf_merger.write(f)

try:
    input_url = input("Enter the URL: ")
    main(input_url)
except Exception as e:
    print(f"An error occurred during execution: {e}")
