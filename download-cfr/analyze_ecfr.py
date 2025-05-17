import requests
import sqlite3
import logging
import json
from typing import List, Dict
from datetime import datetime
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API configuration
BASE_URL = "https://www.ecfr.gov/api"
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2

TODAY = datetime.today().strftime('%Y-%m-%d')

def fetch_with_retries(url: str, retries: int = RETRY_ATTEMPTS) -> Dict:
    """Fetch URL with retries."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json() if url.endswith('.json') else response.text
        except requests.RequestException as e:
            logger.error(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
            if attempt < retries - 1:
                import time
                time.sleep(RETRY_DELAY)
            else:
                raise

def fetch_agencies() -> List[Dict]:
    """Fetch agency data."""
    try:
        return fetch_with_retries(f"{BASE_URL}/admin/v1/agencies.json").get('agencies', [])
    except Exception as e:
        logger.error(f"Error fetching agencies: {e}")
        return []

def fetch_titles() -> List[Dict]:
    """Fetch title metadata."""
    try:
        return fetch_with_retries(f"{BASE_URL}/versioner/v1/titles.json").get('titles', [])
    except Exception as e:
        logger.error(f"Error fetching titles: {e}")
        return []

def fetch_title_structure(title: int, date: str) -> Dict:
    """Fetch title structure."""
    try:
        return fetch_with_retries(f"{BASE_URL}/versioner/v1/structure/{date}/title-{title}.json")
    except Exception as e:
        logger.error(f"Error fetching structure for title {title}: {e}")
        return {}
    
def preload_title_structures(titles: List[Dict], title_dates: Dict[str, str]) -> Dict[int, Dict]:
    title_structures = {}
    for title in tqdm(titles, desc="Preloading title structures", unit="title"):
        title_num = title['number']
        date = title_dates.get(str(title_num), TODAY)
        try:
            structure = fetch_title_structure(title_num, date)
            title_structures[title_num] = build_structure_dict(structure)
        except Exception as e:
            logger.error(f"Failed to preload structure for title {title_num}: {e}")
    return title_structures

def build_structure_dict(structure: Dict) -> Dict:
    """Build nested dictionary for O(1) lookups."""
    title_dict = {'subtitles': {}, 'chapters': {}}
    
    for item in structure.get('children', []):
        item_type = item.get('type')
        item_id = item.get('identifier')
        if not item_id:
            continue

        if item_type == 'subtitle':
            subtitle_dict = title_dict['subtitles'][item_id] = {
                'size': item.get('size', 0),
                'chapters': {}
            }
            for chapter in item.get('children', []):
                if chapter.get('type') != 'chapter':
                    continue
                chapter_id = chapter.get('identifier')
                if not chapter_id:
                    continue
                chapter_dict = subtitle_dict['chapters'][chapter_id] = {
                    'size': chapter.get('size', 0),
                    'subchapters': {},
                    'parts': {}
                }
                for subchapter in chapter.get('children', []):
                    subchapter_id = subchapter.get('identifier')
                    if subchapter_id:
                        chapter_dict['subchapters'][subchapter_id] = {
                            'size': subchapter.get('size', 0),
                            'parts': {}
                        }
                    for part in subchapter.get('children', []):
                        if part.get('type') != 'part' or part.get('reserved'):
                            continue
                        part_id = part.get('identifier')
                        part_size = part.get('size', 0)
                        if subchapter_id:
                            chapter_dict['subchapters'][subchapter_id]['parts'][part_id] = part_size
                        else:
                            chapter_dict['parts'][part_id] = part_size

        elif item_type == 'chapter':
            chapter_dict = title_dict['chapters'][item_id] = {
                'size': item.get('size', 0),
                'subchapters': {},
                'parts': {}
            }
            for subchapter in item.get('children', []):
                subchapter_id = subchapter.get('identifier')
                if subchapter_id:
                    chapter_dict['subchapters'][subchapter_id] = {
                        'size': subchapter.get('size', 0),
                        'parts': {}
                    }
                for part in subchapter.get('children', []):
                    if part.get('type') != 'part' or part.get('reserved'):
                        continue
                    part_id = part.get('identifier')
                    part_size = part.get('size', 0)
                    if subchapter_id:
                        chapter_dict['subchapters'][subchapter_id]['parts'][part_id] = part_size
                    else:
                        chapter_dict['parts'][part_id] = part_size

    return title_dict

def log_cfr_reference_error(agency_name: str, cfr_reference: Dict, error_message: str, conn: sqlite3.Connection):
    """Log CFR reference error."""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cfr_reference_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agency_name TEXT,
                cfr_reference TEXT,
                error_message TEXT,
                timestamp TEXT
            )
        ''')
        cursor.execute('''
            INSERT INTO cfr_reference_errors (agency_name, cfr_reference, error_message, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (agency_name, str(cfr_reference), error_message, TODAY))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error logging CFR reference error for {agency_name}: {e}")

def process_agency_cfr_references(relevant_refs: List[Dict], title_structures: Dict[int, Dict], title_dates: Dict[str, str], agency_name: str, db_conn: sqlite3.Connection) -> int:
    """Validate cfr_references using bottom-up approach."""
    word_count = 0
    if not relevant_refs:
        error_message = f"No cfr_references provided for agency {agency_name}"
        logger.error(error_message)
        log_cfr_reference_error(agency_name, {}, error_message, db_conn)
        return word_count

    for ref in relevant_refs:
        title = ref.get('title')
        subtitle = ref.get('subtitle')
        chapter = ref.get('chapter')
        subchapter = ref.get('subchapter')
        part = ref.get('part')
        subpart = ref.get('subpart')
        section = ref.get('section')

        if not isinstance(title, int):
            error_message = f"Invalid title: {title}"
            log_cfr_reference_error(agency_name, ref, error_message, db_conn)
            continue

        date = title_dates.get(str(title), TODAY)
        structure = title_structures.get(title)
        if not structure:
            structure = fetch_title_structure(title, date)
            title_structures[title] = structure = build_structure_dict(structure)

            print(f"${json.dumps(structure, indent=2)}")
            if not structure:
                error_message = f"No structure data for title {title}, date {date}"
                log_cfr_reference_error(agency_name, ref, error_message, db_conn)
                continue

        # Bottom-up: Start with most specific level
        if part:
            if subtitle and chapter:
                if subtitle in structure['subtitles'] and chapter in structure['subtitles'][subtitle]['chapters']:
                    chapter_data = structure['subtitles'][subtitle]['chapters'][chapter]
                    if subchapter and subchapter in chapter_data['subchapters'] and part in chapter_data['subchapters'][subchapter]['parts']:
                        word_count += chapter_data['subchapters'][subchapter]['parts'][part]
                        continue
                    if part in chapter_data['parts']:
                        word_count += chapter_data['parts'][part]
                        continue
            if chapter and chapter in structure['chapters']:
                chapter_data = structure['chapters'][chapter]
                if subchapter and subchapter in chapter_data['subchapters'] and part in chapter_data['subchapters'][subchapter]['parts']:
                    word_count += chapter_data['subchapters'][subchapter]['parts'][part]
                    continue
                if part in chapter_data['parts']:
                    word_count += chapter_data['parts'][part]
                    continue
            error_message = f"Part {part} not found for title {title}, subtitle {subtitle}, chapter {chapter}, subchapter {subchapter}"
            log_cfr_reference_error(agency_name, ref, error_message, db_conn)
            continue

        if subchapter:
            if subtitle and chapter and subtitle in structure['subtitles'] and chapter in structure['subtitles'][subtitle]['chapters']:
                chapter_data = structure['subtitles'][subtitle]['chapters'][chapter]
                if subchapter in chapter_data['subchapters']:
                    word_count += chapter_data['subchapters'][subchapter]['size']
                    continue
            if chapter and chapter in structure['chapters']:
                chapter_data = structure['chapters'][chapter]
                if subchapter in chapter_data['subchapters']:
                    word_count += chapter_data['subchapters'][subchapter]['size']
                    continue
            error_message = f"Subchapter {subchapter} not found for title {title}, subtitle {subtitle}, chapter {chapter}"
            log_cfr_reference_error(agency_name, ref, error_message, db_conn)
            continue

        if chapter:
            if subtitle and subtitle in structure['subtitles'] and chapter in structure['subtitles'][subtitle]['chapters']:
                word_count += structure['subtitles'][subtitle]['chapters'][chapter]['size']
                continue
            if chapter in structure['chapters']:
                word_count += structure['chapters'][chapter]['size']
                continue
            error_message = f"Chapter {chapter} not found for title {title}, subtitle {subtitle}"
            log_cfr_reference_error(agency_name, ref, error_message, db_conn)
            continue

        if subtitle and subtitle in structure['subtitles']:
            word_count += structure['subtitles'][subtitle]['size']
            continue
        if subtitle:
            error_message = f"Subtitle {subtitle} not found for title {title}"
            log_cfr_reference_error(agency_name, ref, error_message, db_conn)
            continue

        error_message = f"No valid subtitle or chapter specified for title {title}"
        log_cfr_reference_error(agency_name, ref, error_message, db_conn)

        # Log errors for unsupported levels
        if subpart or section:
            error_message = f"Subpart {subpart} or section {section} not supported"
            log_cfr_reference_error(agency_name, ref, error_message, db_conn)

    return word_count

def process_agency_and_children(agency: Dict, title_structures: Dict[int, Dict], title_dates: Dict[str, str], db_conn: sqlite3.Connection, results: List[Dict]):
    """Process agency and children recursively."""
    agency_name = agency.get('display_name', 'Unknown Agency')
    relevant_refs = agency.get('cfr_references', [])
    word_count = process_agency_cfr_references(relevant_refs, title_structures, title_dates, agency_name, db_conn)
    results.append({
        'name': agency_name,
        'short_name': agency.get('short_name', ''),
        'slug': agency.get('slug', ''),
        'cfr_references': relevant_refs,
        'sub_agencies': len(agency.get('children', [])),
        'word_count': word_count
    })

    for child in agency.get('children', []):
        process_agency_and_children(child, title_structures, title_dates, db_conn, results)

def analyze_ecfr() -> List[Dict]:
    """Analyze eCFR data."""
    agencies = fetch_agencies()
    titles = fetch_titles()
    if not agencies or not titles:
        logger.error("Failed to fetch agencies or titles")
        return []

    title_dates = {str(t['number']): t.get('latest_amended_on') or t.get('up_to_date_as_of') for t in titles}
    title_structures = preload_title_structures(titles, title_dates)
    results = []

    db_path = 'ecfr_analysis.db'
    conn = sqlite3.connect(db_path)

    for agency in tqdm(agencies, desc="Processing agencies", unit="agency"):
        try:
            process_agency_and_children(agency, title_structures, title_dates, conn, results)
        except Exception as e:
            logger.error(f"Error processing agency {agency.get('display_name', 'Unknown Agency')}: {e}")

    conn.close()
    return results

def save_to_database(data: List[Dict]):
    """Save results to SQLite."""
    try:
        db_path = 'ecfr_analysis.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agencies (
                name TEXT PRIMARY KEY,
                short_name TEXT,
                slug TEXT,
                cfr_references TEXT,
                sub_agencies INTEGER,
                word_count INTEGER
            )
        ''')
        for agency in data:
            cursor.execute('''
                INSERT OR REPLACE INTO agencies (name, short_name, slug, cfr_references, sub_agencies, word_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                agency['name'],
                agency['short_name'],
                agency['slug'],
                str(agency['cfr_references']),
                agency['sub_agencies'],
                agency['word_count']
            ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving to database: {e}")

def main():
    """Run analysis and save results."""
    try:
        results = analyze_ecfr()
        save_to_database(results)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")

if __name__ == "__main__":
    main()