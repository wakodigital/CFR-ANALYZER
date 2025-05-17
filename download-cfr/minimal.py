import requests
import json
from typing import List, Dict, Tuple
from datetime import datetime
import sqlite3
from tqdm import tqdm

BASE_URL = "https://www.ecfr.gov/api"

def get_titles() -> List[Dict]:
    """Fetch all titles from the eCFR API."""
    url = "/versioner/v1/titles.json"
    try:
        response = requests.get(BASE_URL + url, timeout=10)
        response.raise_for_status()
        data = response.json()
        titles = data.get("titles", [])
        print(f"Fetched {len(titles)} titles")
        return titles
    except requests.RequestException as e:
        print(f"Error fetching titles: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing titles JSON: {e}")
        return []

def get_agencies() -> List[Dict]:
    """Fetch all agencies from the eCFR API."""
    url = "/admin/v1/agencies.json"
    try:
        response = requests.get(BASE_URL + url, timeout=10)
        response.raise_for_status()
        data = response.json()
        agencies = data.get("agencies", [])
        print(f"Fetched {len(agencies)} agencies")
        return agencies
    except requests.RequestException as e:
        print(f"Error fetching agencies: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing agencies JSON: {e}")
        return []

def get_agency_ref_structure(date: str, title: int) -> Dict:
    """Fetch the structure for a given title and date."""
    url = f"/versioner/v1/structure/{date}/title-{title}.json"
    print(f"Requesting: {url}")
    try:
        response = requests.get(BASE_URL + url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            structure = data
            if isinstance(structure, dict) and structure.get("children"):
                return structure
            else:
                print(f"Warning: 'structure' is empty or invalid: {structure}")
                return {}
        else:
            print(f"Error: Non-200 status code: {response.status_code}")
            return {}
    except requests.RequestException as e:
        print(f"Error fetching structure: {e}")
        return {}
    except ValueError as e:
        print(f"Error parsing structure JSON: {e}")
        return {}
    
def build_query_string(ref: Dict) -> str:
    """Build a query string from the CFR reference dictionary."""
    query_parts = []
    if ref.get("subtitle"):
        query_parts.append(f"subtitle={ref['subtitle']}")
    if ref.get("chapter"):
        query_parts.append(f"chapter={ref['chapter']}")
    if ref.get("subchapter"):
        query_parts.append(f"subchapter={ref['subchapter']}")
    if ref.get("part"):
        query_parts.append(f"part={ref['part']}")
    query_string = "?" + "&".join(query_parts) if query_parts else ""
    return query_string

def fetch_ancestry_structure(date: str, title: int, ref: Dict) -> List[Dict]:
    """Fetch the ancestry structure for a given title, date, and CFR reference."""
    query_string = build_query_string(ref)
    url = f"/versioner/v1/ancestry/{date}/title-{title}.json{query_string}"
    print(f"Requesting: {BASE_URL}{url}")
    try:
        response = requests.get(BASE_URL + url, timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Raw response (first 1000 chars): {json.dumps(data)[:1000]}...")
            ancestors = data.get("ancestors", [])
            print(f"Ancestry structure fetched with {len(ancestors)} ancestors")
            return ancestors
        else:
            print(f"Error: Non-200 status code: {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"Error fetching ancestry structure: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing ancestry JSON: {e}")
        return []

def get_agency_ref_structure(date: str, title: int, ref: Dict) -> Dict:
    """Fetch the structure for a given title, date, and CFR reference."""
    query_string = build_query_string(ref)
    url = f"/versioner/v1/structure/{date}/title-{title}.json{query_string}"
    print(f"Requesting: {BASE_URL}{url}")
    try:
        response = requests.get(BASE_URL + url, timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Raw response (first 1000 chars): {json.dumps(data)[:1000]}...")
            structure = data.get("structure", {})
            # Extract ancestry_structure if present
            ancestry_structure = data.get("ancestors", [])
            if isinstance(structure, dict):
                print(f"Structure found with {len(structure.get('children', []))} children")
                return {"structure": structure, "ancestors": ancestry_structure}
            else:
                print(f"Warning: 'structure' is empty or invalid: {structure}")
                return {"structure": {}, "ancestors": ancestry_structure}
        else:
            print(f"Error: Non-200 status code: {response.status_code}")
            return {"structure": {}, "ancestors": []}
    except requests.RequestException as e:
        print(f"Error fetching structure: {e}")
        return {"structure": {}, "ancestors": []}
    except ValueError as e:
        print(f"Error parsing structure JSON: {e}")
        return {"structure": {}, "ancestors": []}


def cfr_ref_to_tuple(ref: Dict) -> Tuple:
    """Convert a CFR reference to a tuple for consistent comparison."""
    return tuple((k, ref[k]) for k in sorted(ref.keys()))

def parse_ancestry(ancestors: List[Dict], ref: Tuple) -> int:
    """Parse the ancestry structure to find the size of the deepest level in the CFR reference."""
    if not ancestors or not ref:
        print("Warning: No ancestors or reference to parse")
        return 0

    # Convert ref tuple to dict
    ref_dict = dict(ref)
    title = ref_dict.get("title")
    subtitle = str(ref_dict.get("subtitle")) if ref_dict.get("subtitle") else None
    chapter = str(ref_dict.get("chapter")) if ref_dict.get("chapter") else None
    subchapter = str(ref_dict.get("subchapter")) if ref_dict.get("subchapter") else None
    part = str(ref_dict.get("part")) if ref_dict.get("part") else None
    subpart = str(ref_dict.get("subpart")) if ref_dict.get("subpart") else None
    section = str(ref_dict.get("section")) if ref_dict.get("section") else None

    print(f"Parsing ref: title={title}, subtitle={subtitle}, chapter={chapter}, subchapter={subchapter}, part={part}, subpart={subpart}, section={section}")

    # Determine the deepest level specified in the reference
    deepest_level = "title"
    deepest_id = str(title)
    if section:
        deepest_level = "section"
        deepest_id = section
    elif subpart:
        deepest_level = "subpart"
        deepest_id = subpart
    elif part:
        deepest_level = "part"
        deepest_id = part
    elif subchapter:
        deepest_level = "subchapter"
        deepest_id = subchapter
    elif chapter:
        deepest_level = "chapter"
        deepest_id = chapter
    elif subtitle:
        deepest_level = "subtitle"
        deepest_id = subtitle

    print(f"Deepest level: {deepest_level}, ID: {deepest_id}")

    # Find the deepest level in ancestors
    for ancestor in ancestors:
        ancestor_type = ancestor.get("type")
        ancestor_id = str(ancestor.get("identifier"))
        if ancestor_type == deepest_level and ancestor_id == deepest_id:
            size = ancestor.get("size", 0)
            print(f"Found deepest level ({deepest_level} {deepest_id}) in ancestors, size={size}")
            return size

    print(f"Error: Deepest level ({deepest_level} {deepest_id}) not found in ancestors")
    return 0

def parse_data(data: Dict, ref: Tuple) -> int:
    """Parse the data structure using identifiers from the CFR reference. Return size of the deepest level."""
    if not data or not ref:
        print("Warning: No data or reference to parse")
        return 0

    # Extract structure and ancestors
    structure = data.get("structure", {})
    ancestors = data.get("ancestors", [])

    # Convert ref tuple to dict
    ref_dict = dict(ref)
    title = ref_dict.get("title")
    subtitle = str(ref_dict.get("subtitle")) if ref_dict.get("subtitle") else None
    chapter = str(ref_dict.get("chapter")) if ref_dict.get("chapter") else None
    subchapter = str(ref_dict.get("subchapter")) if ref_dict.get("subchapter") else None
    part = str(ref_dict.get("part")) if ref_dict.get("part") else None
    subpart = str(ref_dict.get("subpart")) if ref_dict.get("subpart") else None
    section = str(ref_dict.get("section")) if ref_dict.get("section") else None

    print(f"Parsing ref: title={title}, subtitle={subtitle}, chapter={chapter}, subchapter={subchapter}, part={part}, subpart={subpart}, section={section}")

    # Determine the deepest level specified in the reference
    deepest_level = "title"
    deepest_id = str(title)
    if section:
        deepest_level = "section"
        deepest_id = section
    elif subpart:
        deepest_level = "subpart"
        deepest_id = subpart
    elif part:
        deepest_level = "part"
        deepest_id = part
    elif subchapter:
        deepest_level = "subchapter"
        deepest_id = subchapter
    elif chapter:
        deepest_level = "chapter"
        deepest_id = chapter
    elif subtitle:
        deepest_level = "subtitle"
        deepest_id = subtitle

    print(f"Deepest level: {deepest_level}, ID: {deepest_id}")

    # Try using ancestors first if available
    if ancestors:
        print(f"Using ancestry_structure with {len(ancestors)} ancestors")
        for ancestor in ancestors:
            ancestor_type = ancestor.get("type")
            ancestor_id = str(ancestor.get("identifier"))
            if ancestor_type == deepest_level and ancestor_id == deepest_id:
                size = ancestor.get("size", 0)
                print(f"Found deepest level ({deepest_level} {deepest_id}) in ancestors, size={size}")
                return size
        print(f"Warning: Deepest level ({deepest_level} {deepest_id}) not found in ancestors, falling back to structure")

    # Fallback to navigating the structure
    if not structure:
        print("Error: No structure provided for fallback navigation")
        return 0

    current_level = structure
    current_type = current_level.get("type", "title")

    # Verify title
    if str(current_level.get("identifier")) != str(title):
        print(f"Error: Title mismatch. Expected {title}, found {current_level.get('identifier')}")
        return 0

    # Navigate to subtitle
    if subtitle:
        found = False
        for child in current_level.get("children", []):
            if child.get("type") == "subtitle" and str(child.get("identifier")) == subtitle:
                current_level = child
                current_type = "subtitle"
                print(f"Navigated to subtitle {subtitle}")
                found = True
                break
        if not found:
            print(f"Error: Subtitle {subtitle} not found in title {title}")
            return 0
        if deepest_level == "subtitle":
            size = current_level.get("size", 0)
            print(f"Reached deepest level (subtitle {subtitle}), size={size}")
            return size

    # Navigate to chapter
    if chapter:
        found = False
        for child in current_level.get("children", []):
            if child.get("type") == "chapter" and str(child.get("identifier")) == chapter:
                current_level = child
                current_type = "chapter"
                print(f"Navigated to chapter {chapter}")
                found = True
                break
        if not found:
            print(f"Error: Chapter {chapter} not found in {current_type} {subtitle or title}")
            return 0
        if deepest_level == "chapter":
            size = current_level.get("size", 0)
            print(f"Reached deepest level (chapter {chapter}), size={size}")
            return size

    # Navigate to subchapter
    if subchapter:
        found = False
        for child in current_level.get("children", []):
            if child.get("type") == "subchapter" and str(child.get("identifier")) == subchapter:
                current_level = child
                current_type = "subchapter"
                print(f"Navigated to subchapter {subchapter}")
                found = True
                break
        if not found:
            print(f"Error: Subchapter {subchapter} not found in chapter {chapter}")
            return 0
        if deepest_level == "subchapter":
            size = current_level.get("size", 0)
            print(f"Reached deepest level (subchapter {subchapter}), size={size}")
            return size

    # Navigate to part
    if part:
        found = False
        for child in current_level.get("children", []):
            if child.get("type") == "part" and str(child.get("identifier")) == part:
                current_level = child
                current_type = "part"
                print(f"Navigated to part {part}")
                found = True
                break
        if not found:
            print(f"Error: Part {part} not found in {current_type} {subchapter or chapter}")
            return 0
        if deepest_level == "part":
            size = current_level.get("size", 0)
            print(f"Reached deepest level (part {part}), size={size}")
            return size

    # Navigate to subpart
    if subpart:
        found = False
        for child in current_level.get("children", []):
            if child.get("type") == "subpart" and str(child.get("identifier")) == subpart:
                current_level = child
                current_type = "subpart"
                print(f"Navigated to subpart {subpart}")
                found = True
                break
        if not found:
            print(f"Error: Subpart {subpart} not found in part {part}")
            return 0
        if deepest_level == "subpart":
            size = current_level.get("size", 0)
            print(f"Reached deepest level (subpart {subpart}), size={size}")
            return size

    # Navigate to section
    if section:
        found = False
        for child in current_level.get("children", []):
            if child.get("type") == "section" and str(child.get("identifier")) == section:
                current_level = child
                current_type = "section"
                print(f"Navigated to section {section}")
                found = True
                break
        if not found:
            print(f"Error: Section {section} not found in {current_type} {subpart or part}")
            return 0
        if deepest_level == "section":
            size = current_level.get("size", 0)
            print(f"Reached deepest level (section {section}), size={size}")
            return size

    # If only title is specified, return its size
    if deepest_level == "title":
        size = current_level.get("size", 0)
        print(f"Reached deepest level (title {title}), size={size}")
        return size

    print(f"Error: No valid deepest level found")
    return 0

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
    # Fetch titles and build title-to-date mapping
    titles = get_titles()
    titles_ref = {}
    if titles:
        for title in titles:
            title_number = title.get("number")
            title_date = title.get("latest_amended_on") or title.get("up_to_date_as_of")
            if title_number and title_date:
                titles_ref[title_number] = title_date
        if titles_ref:
            first_title = next(iter(titles_ref.items()))
            print(f"First Title and Latest Amendment Date: {json.dumps({first_title[0]: first_title[1]}, indent=2)}")
        else:
            print("No valid titles found.")
    else:
        print("No titles found or an error occurred.")
        return

    # Fetch agencies and build agency-to-CFR-references mapping
    agencies = get_agencies()
    agency_refs = {}
    if agencies:
        for agency in agencies:
            agency_name = agency.get("name")
            cfr_refs = agency.get("cfr_references", [])
            agency_refs[agency_name] = cfr_refs
            children = agency.get("children", [])
            for child in children:
                child_name = child.get("name")
                child_cfr_refs = child.get("cfr_references", [])
                agency_refs[child_name] = child_cfr_refs
        if agency_refs:
            first_agency = next(iter(agency_refs.items()))
            print(f"First Agency and CFR References: {json.dumps({first_agency[0]: first_agency[1]}, indent=2)}")
        else:
            print("No valid agencies found.")
    else:
        print("No agencies found or an error occurred.")
        return

    # Process each agency’s CFR references
    total_refs = sum(len(refs) for refs in agency_refs.values())
    with tqdm(total=total_refs, desc="Processing CFR References") as pbar:
        for agency_name, refs in agency_refs.items():
            for ref in refs:
                ref_tuple = cfr_ref_to_tuple(ref)
                title = ref.get("title")
                date = titles_ref.get(title)
                if title and date:
                    ancestors = fetch_ancestry_structure(date, title, ref)
                    if ancestors:
                        print(f"Agency: {agency_name}, CFR Reference: {ref_tuple}, Ancestors: {len(ancestors)}")
                        word_count = parse_ancestry(ancestors, ref_tuple)
                        print(f"Word count for {agency_name}: {word_count}")
                        results = {
                            "name": agency_name,
                            "short_name": ref.get("short_name"),
                            "slug": ref.get("slug"),
                            "cfr_references": ref_tuple,
                            "sub_agencies": len(refs),
                            "word_count": word_count
                        }
                        save_to_database([results])
                    else:
                        print(f"Ancestry structure not found for Agency: {agency_name}, Title: {title}, Date: {date}")
                else:
                    print(f"Skipping ref for {agency_name}: Missing title ({title})")
                pbar.update(1)
    print("Processing complete.")
if __name__ == "__main__":
    main()