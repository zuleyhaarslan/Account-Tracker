from bs4 import BeautifulSoup
import hashlib

def extract_page_snapshot(html_content: str) -> str:
    """
    Cleans structural markup noise and extracts a textual snapshot.
    Can be adjusted to target explicit notification selectors.
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Strip non-text noise blocks before checking for content updates
    for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
        script_or_style.extract()
        
    # Extract visible plain-text segments
    text_content = soup.get_text(separator=" ")
    lines = [line.strip() for line in text_content.splitlines()]
    cleaned_chunks = [chunk for chunk in lines if chunk]
    
    # Return a condensed text block of the target environment view
    return " ".join(cleaned_chunks)

def detect_delta_changes(new_html: str, old_snapshot_text: str) -> tuple[bool, str]:
    """Compares the new page content against the last saved snapshot."""
    if not new_html:
        return False, old_snapshot_text
        
    new_snapshot = extract_page_snapshot(new_html)
    
    if not old_snapshot_text:
        # Initial check baseline establish step
        return False, new_snapshot
        
    # Generate hashes to check for modifications
    hash_old = hashlib.sha256(old_snapshot_text.encode('utf-8')).hexdigest()
    hash_new = hashlib.sha256(new_snapshot.encode('utf-8')).hexdigest()
    
    is_changed = (hash_old != hash_new)
    return is_changed, new_snapshot