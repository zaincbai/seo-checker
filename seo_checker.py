#!/usr/bin/env python3
"""
SEO Checker Tool
A comprehensive Python script to analyze websites and generate SEO reports.
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import logging
import os
import re
from urllib.parse import urlparse, urljoin, urldefrag
from datetime import datetime
import json
from typing import List, Dict, Any, Optional
import argparse


class SEOChecker:
    def __init__(self, log_level: str = "INFO"):
        """Initialize the SEO checker with logging configuration."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create directories
        os.makedirs('logs', exist_ok=True)
        os.makedirs('reports', exist_ok=True)
        
        # Setup logging
        self.setup_logging(log_level)
        
    def setup_logging(self, log_level: str):
        """Setup logging configuration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"logs/seo_checker_{timestamp}.log"
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"SEO Checker initialized. Log file: {log_filename}")
    
    def fetch_page(self, url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Fetch a webpage and return content with timing information."""
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=timeout, allow_redirects=True)
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    'content': response.text,
                    'load_time': load_time,
                    'status_code': response.status_code,
                    'final_url': response.url,
                    'headers': dict(response.headers)
                }
            else:
                self.logger.warning(f"HTTP {response.status_code} for {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def parse_html(self, content: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup."""
        return BeautifulSoup(content, 'html.parser')
    
    def extract_title(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract page title information."""
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""
        
        return {
            'title': title,
            'title_length': len(title),
            'title_exists': bool(title),
            'title_optimal': 30 <= len(title) <= 60
        }
    
    def extract_meta_description(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract meta description information."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '').strip() if meta_desc else ""
        
        return {
            'meta_description': description,
            'meta_description_length': len(description),
            'meta_description_exists': bool(description),
            'meta_description_optimal': 120 <= len(description) <= 160
        }
    
    def extract_canonical_url(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract canonical URL information."""
        canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
        canonical_url = canonical_tag.get('href', '') if canonical_tag else ""
        
        return {
            'canonical_url': canonical_url,
            'canonical_exists': bool(canonical_url)
        }
    
    def extract_headings(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract heading structure information."""
        headings = {}
        heading_counts = {}
        
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            headings[f'h{i}'] = [tag.get_text().strip() for tag in h_tags]
            heading_counts[f'h{i}_count'] = len(h_tags)
        
        # Check for proper heading structure
        h1_count = heading_counts.get('h1_count', 0)
        has_h1 = h1_count > 0
        multiple_h1 = h1_count > 1
        
        return {
            'headings': headings,
            'heading_counts': heading_counts,
            'has_h1': has_h1,
            'multiple_h1': multiple_h1,
            'h1_optimal': h1_count == 1
        }
    
    def extract_word_count(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract word count from visible content."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        word_count = len(text.split())
        
        return {
            'word_count': word_count,
            'content_length_optimal': word_count >= 300
        }
    
    def extract_images(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract image information and check for missing alt attributes."""
        images = soup.find_all('img')
        total_images = len(images)
        images_without_alt = 0
        images_with_empty_alt = 0
        
        for img in images:
            alt = img.get('alt', '')
            if not img.has_attr('alt'):
                images_without_alt += 1
            elif not alt.strip():
                images_with_empty_alt += 1
        
        return {
            'total_images': total_images,
            'images_without_alt': images_without_alt,
            'images_with_empty_alt': images_with_empty_alt,
            'images_alt_optimization': (total_images - images_without_alt - images_with_empty_alt) / max(total_images, 1)
        }
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Extract and analyze internal and external links."""
        links = soup.find_all('a', href=True)
        base_domain = urlparse(base_url).netloc
        
        internal_links = []
        external_links = []
        
        for link in links:
            href = link.get('href', '').strip()
            if not href or href.startswith('#'):
                continue
                
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            # Remove fragments
            clean_url = urldefrag(absolute_url)[0]
            
            link_domain = urlparse(clean_url).netloc
            
            if link_domain == base_domain:
                internal_links.append(clean_url)
            else:
                external_links.append(clean_url)
        
        return {
            'total_links': len(links),
            'internal_links': list(set(internal_links)),
            'external_links': list(set(external_links)),
            'internal_links_count': len(set(internal_links)),
            'external_links_count': len(set(external_links))
        }
    
    def check_broken_links(self, links: List[str]) -> Dict[str, Any]:
        """Check for broken links (sample of links to avoid overloading)."""
        broken_links = []
        checked_links = 0
        
        # Limit the number of links to check to avoid long execution times
        links_to_check = links[:20]  # Check first 20 links
        
        for link in links_to_check:
            try:
                response = self.session.head(link, timeout=5, allow_redirects=True)
                if response.status_code >= 400:
                    broken_links.append({
                        'url': link,
                        'status_code': response.status_code
                    })
                checked_links += 1
            except Exception as e:
                broken_links.append({
                    'url': link,
                    'error': str(e)
                })
                checked_links += 1
        
        return {
            'checked_links': checked_links,
            'broken_links': broken_links,
            'broken_links_count': len(broken_links)
        }
    
    def check_robots_and_sitemap(self, base_url: str) -> Dict[str, Any]:
        """Check for robots.txt and sitemap.xml files."""
        parsed_url = urlparse(base_url)
        base_domain_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        robots_url = f"{base_domain_url}/robots.txt"
        sitemap_url = f"{base_domain_url}/sitemap.xml"
        
        robots_exists = False
        sitemap_exists = False
        
        try:
            robots_response = self.session.get(robots_url, timeout=5)
            robots_exists = robots_response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Error checking robots.txt: {str(e)}")
        
        try:
            sitemap_response = self.session.get(sitemap_url, timeout=5)
            sitemap_exists = sitemap_response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Error checking sitemap.xml: {str(e)}")
        
        return {
            'robots_txt_exists': robots_exists,
            'sitemap_xml_exists': sitemap_exists,
            'robots_txt_url': robots_url,
            'sitemap_xml_url': sitemap_url
        }
    
    def extract_social_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract Open Graph and Twitter Card meta tags."""
        og_tags = {}
        twitter_tags = {}
        
        # Open Graph tags
        og_meta_tags = soup.find_all('meta', attrs={'property': re.compile(r'^og:')})
        for tag in og_meta_tags:
            property_name = tag.get('property', '')
            content = tag.get('content', '')
            og_tags[property_name] = content
        
        # Twitter Card tags
        twitter_meta_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')})
        for tag in twitter_meta_tags:
            name = tag.get('name', '')
            content = tag.get('content', '')
            twitter_tags[name] = content
        
        return {
            'og_tags': og_tags,
            'twitter_tags': twitter_tags,
            'og_tags_count': len(og_tags),
            'twitter_tags_count': len(twitter_tags),
            'has_og_title': 'og:title' in og_tags,
            'has_og_description': 'og:description' in og_tags,
            'has_og_image': 'og:image' in og_tags,
            'has_twitter_card': 'twitter:card' in twitter_tags
        }
    
    def extract_backlink_insights(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Extract basic backlink insights from the page content."""
        base_domain = urlparse(base_url).netloc
        
        # Find external links that might be referring to this domain
        external_links = soup.find_all('a', href=True)
        referring_domains = set()
        
        for link in external_links:
            href = link.get('href', '')
            if base_domain in href:
                link_domain = urlparse(href).netloc
                if link_domain != base_domain:
                    referring_domains.add(link_domain)
        
        return {
            'potential_referring_domains': list(referring_domains),
            'referring_domains_count': len(referring_domains)
        }
    
    def analyze_url(self, url: str) -> Dict[str, Any]:
        """Perform comprehensive SEO analysis on a single URL."""
        self.logger.info(f"Analyzing URL: {url}")
        
        # Initialize result
        result = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'analysis_successful': False
        }
        
        try:
            # Fetch page
            page_data = self.fetch_page(url)
            if not page_data:
                result['error'] = "Failed to fetch page"
                return result
            
            result['load_time'] = page_data['load_time']
            result['status_code'] = page_data['status_code']
            result['final_url'] = page_data['final_url']
            
            # Parse HTML
            soup = self.parse_html(page_data['content'])
            
            # Perform SEO checks
            result.update(self.extract_title(soup))
            result.update(self.extract_meta_description(soup))
            result.update(self.extract_canonical_url(soup))
            result.update(self.extract_headings(soup))
            result.update(self.extract_word_count(soup))
            result.update(self.extract_images(soup))
            
            # Link analysis
            links_data = self.extract_links(soup, url)
            result.update(links_data)
            
            # Check for broken links (sample)
            all_links = links_data['internal_links'] + links_data['external_links']
            broken_links_data = self.check_broken_links(all_links)
            result.update(broken_links_data)
            
            # Check robots.txt and sitemap.xml
            result.update(self.check_robots_and_sitemap(url))
            
            # Social meta tags
            result.update(self.extract_social_meta_tags(soup))
            
            # Basic backlink insights
            result.update(self.extract_backlink_insights(soup, url))
            
            result['analysis_successful'] = True
            self.logger.info(f"Successfully analyzed: {url}")
            
        except Exception as e:
            self.logger.error(f"Error analyzing {url}: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    def analyze_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple URLs and return results."""
        results = []
        
        for i, url in enumerate(urls, 1):
            self.logger.info(f"Processing URL {i}/{len(urls)}: {url}")
            result = self.analyze_url(url)
            results.append(result)
            
            # Add a small delay to be respectful
            time.sleep(1)
        
        return results
    
    def save_csv_report(self, results: List[Dict[str, Any]], filename: str):
        """Save results to CSV file."""
        if not results:
            self.logger.warning("No results to save")
            return
        
        # Define CSV columns
        csv_columns = [
            'url', 'timestamp', 'analysis_successful', 'load_time', 'status_code',
            'title', 'title_length', 'title_exists', 'title_optimal',
            'meta_description', 'meta_description_length', 'meta_description_exists', 'meta_description_optimal',
            'canonical_url', 'canonical_exists',
            'has_h1', 'multiple_h1', 'h1_optimal',
            'h1_count', 'h2_count', 'h3_count', 'h4_count', 'h5_count', 'h6_count',
            'word_count', 'content_length_optimal',
            'total_images', 'images_without_alt', 'images_with_empty_alt',
            'total_links', 'internal_links_count', 'external_links_count',
            'broken_links_count', 'robots_txt_exists', 'sitemap_xml_exists',
            'og_tags_count', 'twitter_tags_count', 'has_og_title', 'has_og_description',
            'has_og_image', 'has_twitter_card', 'referring_domains_count'
        ]
        
        filepath = f"reports/{filename}"
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            
            for result in results:
                # Flatten the result data
                row = {}
                for col in csv_columns:
                    if col in result:
                        row[col] = result[col]
                    elif col.endswith('_count') and col.replace('_count', '') in result.get('heading_counts', {}):
                        row[col] = result['heading_counts'][col.replace('_count', '')]
                    else:
                        row[col] = ''
                
                writer.writerow(row)
        
        self.logger.info(f"CSV report saved: {filepath}")
    
    def save_html_report(self, results: List[Dict[str, Any]], filename: str):
        """Save results to HTML file."""
        if not results:
            self.logger.warning("No results to save")
            return
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SEO Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .url-report {{ background-color: white; margin-bottom: 20px; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .url-header {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 15px; }}
                .url-title {{ color: #2c3e50; font-size: 1.2em; font-weight: bold; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
                .metric {{ background-color: #ecf0f1; padding: 10px; border-radius: 5px; }}
                .metric-label {{ font-weight: bold; color: #34495e; }}
                .metric-value {{ margin-top: 5px; }}
                .status-good {{ color: #27ae60; }}
                .status-warning {{ color: #f39c12; }}
                .status-error {{ color: #e74c3c; }}
                .headings {{ margin-top: 15px; }}
                .heading-item {{ background-color: #f8f9fa; padding: 5px 10px; margin: 5px 0; border-left: 4px solid #3498db; }}
                .error {{ background-color: #e74c3c; color: white; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>SEO Analysis Report</h1>
                    <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    <p>Total URLs analyzed: {len(results)}</p>
                </div>
        """
        
        for result in results:
            if not result.get('analysis_successful'):
                html_content += f"""
                <div class="url-report">
                    <div class="url-header">
                        <div class="url-title">{result['url']}</div>
                    </div>
                    <div class="error">
                        Analysis failed: {result.get('error', 'Unknown error')}
                    </div>
                </div>
                """
                continue
            
            html_content += f"""
            <div class="url-report">
                <div class="url-header">
                    <div class="url-title">{result['url']}</div>
                    <div>Load Time: {result.get('load_time', 0):.2f}s | Status: {result.get('status_code', 'N/A')}</div>
                </div>
                
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">Page Title</div>
                        <div class="metric-value">
                            <div class="{'status-good' if result.get('title_optimal') else 'status-warning'}">
                                {result.get('title', 'No title')} ({result.get('title_length', 0)} chars)
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric">
                        <div class="metric-label">Meta Description</div>
                        <div class="metric-value">
                            <div class="{'status-good' if result.get('meta_description_optimal') else 'status-warning'}">
                                {result.get('meta_description', 'No meta description')[:100]}{'...' if len(result.get('meta_description', '')) > 100 else ''} ({result.get('meta_description_length', 0)} chars)
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric">
                        <div class="metric-label">H1 Tags</div>
                        <div class="metric-value">
                            <div class="{'status-good' if result.get('h1_optimal') else 'status-error'}">
                                {result.get('heading_counts', {}).get('h1_count', 0)} H1 tag(s)
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric">
                        <div class="metric-label">Word Count</div>
                        <div class="metric-value">
                            <div class="{'status-good' if result.get('content_length_optimal') else 'status-warning'}">
                                {result.get('word_count', 0)} words
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric">
                        <div class="metric-label">Images</div>
                        <div class="metric-value">
                            {result.get('total_images', 0)} total, {result.get('images_without_alt', 0)} without alt
                        </div>
                    </div>
                    
                    <div class="metric">
                        <div class="metric-label">Links</div>
                        <div class="metric-value">
                            {result.get('internal_links_count', 0)} internal, {result.get('external_links_count', 0)} external
                        </div>
                    </div>
                    
                    <div class="metric">
                        <div class="metric-label">Technical SEO</div>
                        <div class="metric-value">
                            Robots.txt: {'✓' if result.get('robots_txt_exists') else '✗'}<br>
                            Sitemap.xml: {'✓' if result.get('sitemap_xml_exists') else '✗'}<br>
                            Canonical: {'✓' if result.get('canonical_exists') else '✗'}
                        </div>
                    </div>
                    
                    <div class="metric">
                        <div class="metric-label">Social Meta</div>
                        <div class="metric-value">
                            OG tags: {result.get('og_tags_count', 0)}<br>
                            Twitter tags: {result.get('twitter_tags_count', 0)}
                        </div>
                    </div>
                </div>
            """
            
            # Add headings structure
            headings = result.get('headings', {})
            if any(headings.values()):
                html_content += '<div class="headings"><h4>Headings Structure:</h4>'
                for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if headings.get(level):
                        for heading_text in headings[level]:
                            html_content += f'<div class="heading-item"><strong>{level.upper()}:</strong> {heading_text}</div>'
                html_content += '</div>'
            
            html_content += '</div>'
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        filepath = f"reports/{filename}"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML report saved: {filepath}")


def load_urls_from_file(filename: str) -> List[str]:
    """Load URLs from a text file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return urls
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return []


def main():
    """Main function to run the SEO checker."""
    parser = argparse.ArgumentParser(description='SEO Checker Tool')
    parser.add_argument('--urls', '-u', nargs='+', help='URLs to analyze')
    parser.add_argument('--file', '-f', help='File containing URLs to analyze')
    parser.add_argument('--output', '-o', default='seo_report', help='Output filename prefix')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Determine URLs to analyze
    urls = []
    if args.urls:
        urls = args.urls
    elif args.file:
        urls = load_urls_from_file(args.file)
    else:
        # Default URLs for demonstration
        urls = [
            'https://example.com',
            'https://github.com',
            'https://stackoverflow.com'
        ]
        print("No URLs provided. Using default URLs for demonstration.")
    
    if not urls:
        print("No URLs to analyze. Please provide URLs using --urls or --file.")
        return
    
    # Initialize SEO checker
    checker = SEOChecker(log_level=args.log_level)
    
    # Analyze URLs
    print(f"Analyzing {len(urls)} URLs...")
    results = checker.analyze_urls(urls)
    
    # Generate reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{args.output}_{timestamp}.csv"
    html_filename = f"{args.output}_{timestamp}.html"
    
    checker.save_csv_report(results, csv_filename)
    checker.save_html_report(results, html_filename)
    
    # Print summary
    successful_analyses = sum(1 for r in results if r.get('analysis_successful'))
    print(f"\nAnalysis complete!")
    print(f"Successfully analyzed: {successful_analyses}/{len(urls)} URLs")
    print(f"Reports saved:")
    print(f"  - CSV: reports/{csv_filename}")
    print(f"  - HTML: reports/{html_filename}")


if __name__ == "__main__":
    main() 