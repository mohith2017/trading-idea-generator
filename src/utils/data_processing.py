import os
from fpdf import FPDF
from dotenv import load_dotenv
import pandas as pd
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from llama_index.readers.web import SimpleWebPageReader
from .logger_config import logger

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
logger = logger(__name__, 'app.log', level='DEBUG')

def scrape_url(url):
    try:
        documents = SimpleWebPageReader(html_to_text=True).load_data([url])
        logger.debug(documents)
        
        if documents and len(documents) > 0:
            doc = documents[0]
            return {
                'url': url,
                'data': {
                    'text_content': doc.text,
                    'title': doc.metadata.get('title', ''),
                    'meta_description': doc.metadata.get('description', '')
                }
            }
        return None
            
    except Exception as e:
        logger.error(f"Error processing URL {url}: {str(e)}")
        return None
    
def scrape_urls_parallel(all_urls, max_workers=10):
    """
    Parallely scrape multiple URLs using ThreadPoolExecutor to optimize performance
    """
    logger.debug(f"Starting parallel scraping of {len(all_urls)} URLs...")
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scrape_url, url): url for url in all_urls}
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
                if data:
                    results[url] = data
                    logger.debug(f"Successfully scraped: {url}")
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {str(e)}")
    
    logger.debug(f"Completed scraping. Successfully scraped {len(results)} out of {len(all_urls)} URLs")
    return results
    
def create_pdf(filename_data, pdf_output_dir):
    filename, data = filename_data
    pdf = FPDF()
    pdf.set_font("helvetica", size=12)
    
    def clean_text(text):
        if not isinstance(text, str):
            text = str(text)
        text = text.encode('ascii', 'replace').decode('ascii')
        return text
    
    for idx, content in data.items():
        pdf.add_page()
        
        pdf.multi_cell(0, 10, txt=f"Entry {idx}")
        pdf.multi_cell(0, 10, txt=f"Text: {clean_text(content.get('text', ''))[:1000]}")
        pdf.multi_cell(0, 10, txt=f"Full Text: {clean_text(content.get('fullText', ''))[:1000]}")
        
        if 'extracted_urls' in content and content['extracted_urls']:
            pdf.multi_cell(0, 10, txt="\nExtracted URLs:")
            for url_data in content['extracted_urls']:
                pdf.multi_cell(0, 10, txt=f"\nURL: {clean_text(url_data.get('url', ''))}")
                if 'data' in url_data:
                    text_content = clean_text(url_data['data'].get('text_content', ''))[:500]
                    title = clean_text(url_data['data'].get('title', ''))
                    desc = clean_text(url_data['data'].get('meta_description', ''))
                    pdf.multi_cell(0, 10, txt=f"Title: {title}")
                    pdf.multi_cell(0, 10, txt=f"Description: {desc}")
                    pdf.multi_cell(0, 10, txt=f"Content: {text_content}")
    
    pdf_path = os.path.join(pdf_output_dir, f"{filename}")
    try:
        pdf.output(pdf_path)
        logger.debug(f"Created PDF: {pdf_path}")
    except Exception as e:
        logger.error(f"Error creating PDF for {filename}: {str(e)}")
        return None
    return filename

def create_pdfs_parallel(extracted_data, pdf_output_dir, max_workers=4):
    """
    Parallely create PDFs using ProcessPoolExecutor to optimize I/O operations
    """
    logger.debug(f"Starting parallel PDF creation for {len(extracted_data)} files...")
    results = []
    
    pdf_tasks = [(filename.replace('.json', '.pdf'), data) 
                 for filename, data in extracted_data.items()]
    
    for filename, data in pdf_tasks:
        for idx in data:
            if 'extracted_urls' in data[idx]:
                data[idx]['extracted_urls'] = [
                    {
                        'url': url_data.get('url', ''),
                        'data': {
                            'text_content': url_data.get('data', {}).get('text_content', '')[:1000],
                            'title': url_data.get('data', {}).get('title', ''),
                            'meta_description': url_data.get('data', {}).get('meta_description', '')
                        }
                    } if isinstance(url_data, dict) else {}
                    for url_data in data[idx]['extracted_urls']
                ]
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(create_pdf, task, pdf_output_dir): task[0] 
                         for task in pdf_tasks}
        
        for future in concurrent.futures.as_completed(future_to_file):
            filename = future_to_file[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                    logger.debug(f"Successfully created PDF: {filename}")
            except Exception as e:
                logger.error(f"Failed to create PDF {filename}: {str(e)}")
    
    logger.debug(f"Completed PDF creation. Successfully created {len(results)} out of {len(pdf_tasks)} PDFs")
    return results

def extract_data_from_json(): 
    logger.debug("Extracting data from JSON...")
    output_dir = "src/data/downloaded_files/data_dir"
    pdf_output_dir = "src/data/pdf_files"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(pdf_output_dir, exist_ok=True)

    if os.path.exists(pdf_output_dir) and len(os.listdir(pdf_output_dir)) > 0:
        logger.debug("PDF files already exist, skipping extraction...")
        pdf_files = {}
        for filename in os.listdir(pdf_output_dir):
            if filename.endswith('.pdf'):
                file_path = os.path.join(pdf_output_dir, filename)
                pdf_files[filename] = {}
                pdf_files[filename][0] = {
                    "text": filename,
                    "fullText": file_path 
                }
        return pdf_files

    logger.debug("Loading JSON files into DataFrame...")
    dfs = []
    for filename in os.listdir(output_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(output_dir, filename)
            df = pd.read_json(file_path)
            df['filename'] = filename
            dfs.append(df)
    
    combined_df = pd.concat(dfs, ignore_index=True)
    
    logger.debug("Extracting URLs from entities...")
    extracted_data = {}
    all_urls = set()
    url_metadata = {}
    
    for _, row in combined_df.iterrows():
        filename = row['filename']
        if filename not in extracted_data:
            extracted_data[filename] = {}
        
        idx = len(extracted_data[filename])
        extracted_data[filename][idx] = {
            'text': row['text'],
            'fullText': row['fullText'],
            'extracted_urls': []
        }
        
        if 'author' in row and 'entities' in row['author']:
            entities = row['author']['entities']
            if 'url' in entities and 'urls' in entities['url']:
                for url_obj in entities['url']['urls']:
                    expanded_url = url_obj['expanded_url']
                    if not expanded_url.startswith('https://t.co/'):
                        if expanded_url not in all_urls:
                            all_urls.add(expanded_url)
                            url_metadata[expanded_url] = (filename, idx)

    all_urls = list(all_urls)
    scraped_data = scrape_urls_parallel(all_urls)
    for url, scraped_result in scraped_data.items():
        if url in url_metadata:
            filename, idx = url_metadata[url]
            extracted_data[filename][idx]['extracted_urls'].append(scraped_result)

    logger.debug("Creating PDFs in parallel...")
    create_pdfs_parallel(extracted_data, pdf_output_dir)
    
    return extracted_data
