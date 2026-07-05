import sys
import os
import re
import time
import json
import threading
from dotenv import load_dotenv
import pyperclip
import spacy
from spacy.matcher import PhraseMatcher
from spacy.util import filter_spans

# Ensure parent directory is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import database
from cliche_dict import CLICHES
import gemini_client

# Load environment variables
load_dotenv()

# Thread safety lock for stdout
stdout_lock = threading.Lock()

def send_json(data):
    """Sends JSON-encoded message to stdout safely."""
    with stdout_lock:
        sys.stdout.write(json.dumps(data) + "\n")
        sys.stdout.flush()

# Load spaCy model
nlp = None
matcher = None

def init_nlp():
    global nlp, matcher
    try:
        nlp = spacy.load("en_core_web_sm")
        matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        # Build patterns from cliche list
        patterns = [nlp.make_doc(text) for text in CLICHES]
        matcher.add("CLICHE", patterns)
    except Exception as e:
        send_json({"type": "error", "message": f"Failed to initialize NLP (spaCy): {str(e)}"})
        sys.exit(1)

def compute_robot_score(text):
    """
    Computes the Corporate Robot Score for the given text.
    Score = (Flagged Jargon Tokens / Total Word Count) * 100
    Returns: (score, list of clichés found)
    """
    if not text.strip():
        return 0.0, []

    doc = nlp(text)
    
    # Exclude punctuation and whitespace tokens from total count
    words = [t for t in doc if not t.is_punct and not t.is_space]
    total_word_count = len(words)
    
    if total_word_count == 0:
        return 0.0, []
        
    matches = matcher(doc)
    
    # Filter overlapping matches to get distinct spans
    spans = [doc[start:end] for _, start, end in matches]
    filtered_spans = filter_spans(spans)
    
    # Count the total tokens that fell within a flagged cliché span
    flagged_token_count = sum(len(span) for span in filtered_spans)
    
    # Calculate score
    score = (flagged_token_count / total_word_count) * 100
    score = round(score, 1)
    
    # Collect unique cliché phrases found for display
    cliches_found = list(set([span.text.strip() for span in filtered_spans]))
    
    return score, cliches_found

# Regex trigger conditions
TRIGGER_REGEX = re.compile(r"(hiring manager|apply for the position|resume enclosed|to whom it may concern)", re.IGNORECASE)

def clipboard_poller():
    """Polls the OS clipboard for cover-letter matching keywords."""
    last_clipboard = ""
    while True:
        try:
            current_text = pyperclip.paste()
            # If the clipboard changed and has content
            if current_text and current_text != last_clipboard:
                last_clipboard = current_text
                
                # Check regex trigger
                if TRIGGER_REGEX.search(current_text):
                    score, cliches = compute_robot_score(current_text)
                    send_json({
                        "type": "clipboard_trigger",
                        "text": current_text,
                        "score": score,
                        "cliches": cliches
                    })
        except Exception:
            # Clipboard read can fail if clipboard is empty or locked by OS
            pass
        time.sleep(1.0)

def handle_stdin():
    """Reads command JSON lines from stdin and processes them."""
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            cmd = json.loads(line)
            cmd_type = cmd.get("type")
            
            if cmd_type == "request_rewrite":
                text = cmd.get("text", "")
                company_name = cmd.get("company_name", "Unknown Company")
                
                # First get robot score locally
                score, cliches = compute_robot_score(text)
                
                # Run Gemini rewrite
                rewrite_data = gemini_client.rewrite_cover_letter(text, score)
                
                if rewrite_data.get("status") == "success":
                    cleaned_text = rewrite_data.get("rewritten_output", "")
                    # Extract flags as cliché info
                    flags = rewrite_data.get("flags", [])
                    
                    # Save to Database
                    db_id = database.save_cover_letter(
                        company_name=company_name,
                        original_text=text,
                        cleaned_text=cleaned_text,
                        robot_score=score,
                        clichés_found=flags
                    )
                    
                    # Send result back
                    send_json({
                        "type": "rewrite_result",
                        "status": "success",
                        "original_score": score,
                        "rewritten_output": cleaned_text,
                        "flags": flags,
                        "db_id": db_id
                    })
                    
                    # Send updated history list automatically
                    send_json({
                        "type": "history_list",
                        "items": database.get_all_entries()
                    })
                else:
                    send_json({
                        "type": "error",
                        "message": rewrite_data.get("message", "Unknown Gemini Error")
                    })
                    
            elif cmd_type == "get_history":
                send_json({
                    "type": "history_list",
                    "items": database.get_all_entries()
                })
                
            elif cmd_type == "delete_history_item":
                entry_id = cmd.get("id")
                if entry_id is not None:
                    database.delete_entry(entry_id)
                    send_json({
                        "type": "history_list",
                        "items": database.get_all_entries()
                    })
                    
        except Exception as e:
            send_json({"type": "error", "message": f"Exception processing stdin command: {str(e)}"})

def main():
    # Initialize DB
    database.init_db()
    
    # Initialize NLP
    init_nlp()
    
    # Start clipboard thread
    t = threading.Thread(target=clipboard_poller, daemon=True)
    t.start()
    
    # Listen to standard input
    handle_stdin()

if __name__ == "__main__":
    main()
