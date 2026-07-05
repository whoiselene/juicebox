import sys
import os
import unittest
import json

# Ensure parent and backend directories are in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import database
import cliche_dict
import daemon
import gemini_client

class TestPapayaBackend(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Initialize DB (creates papaya.db)
        database.init_db()
        # Initialize spaCy
        daemon.init_nlp()
        
    def test_cliche_jargon_score(self):
        print("\n--- Testing spaCy local cliché scoring ---")
        
        # Test Case 1: Simple clean text (should have 0% score)
        text_clean = "I built a web application using vanilla HTML and CSS to display database metrics."
        score, cliches = daemon.compute_robot_score(text_clean)
        print(f"Clean text: '{text_clean}'\n-> Score: {score}%, clichés found: {cliches}")
        self.assertEqual(score, 0.0)
        self.assertEqual(len(cliches), 0)
        
        # Test Case 2: Highly corporate text (should have >15% score)
        text_jargon = "To whom it may concern, I am a highly motivated results-oriented leader. I have a proven track record of deep dive discussions."
        # words in text: 
        # [To, whom, it, may, concern, I, am, a, highly, motivated, results-oriented, leader, I, have, a, proven, track, record, of, deep, dive, discussions] = 22 words (excluding punctuation)
        # matched cliches: 
        # - "to whom it may concern" (5 tokens)
        # - "highly motivated" (2 tokens)
        # - "results-oriented" (2 tokens or 3 if split, but let's count matching tokens)
        # - "proven track record" (3 tokens)
        # - "deep dive" (2 tokens)
        # Expected flagged tokens = 5+2+2+3+2 = 14 tokens
        # Score approx: 14/22 * 100 = 63.6%
        score, cliches = daemon.compute_robot_score(text_jargon)
        print(f"Jargon text: '{text_jargon}'\n-> Score: {score}%, clichés found: {cliches}")
        self.assertGreater(score, 15.0)
        self.assertIn("highly motivated", cliches)
        self.assertIn("proven track record", cliches)
        
    def test_sqlite_database(self):
        print("\n--- Testing SQLite persistence layer ---")
        
        company = "TestCorp"
        original = "Draft cover letter with some jargon."
        cleaned = "Refined, authentic, and narrative cover letter."
        score = 18.5
        cliches = [{"phrase": "some jargon", "reason": "Avoid filler words."}]
        
        # 1. Save entry
        db_id = database.save_cover_letter(company, original, cleaned, score, cliches)
        print(f"Saved database entry, ID: {db_id}")
        self.assertIsNotNone(db_id)
        
        # 2. Retrieve entries
        entries = database.get_all_entries()
        print(f"Retrieved {len(entries)} entries from SQLite")
        self.assertGreater(len(entries), 0)
        
        # Find our saved entry
        test_entry = next((e for e in entries if e["id"] == db_id), None)
        self.assertIsNotNone(test_entry)
        self.assertEqual(test_entry["company_name"], company)
        self.assertEqual(test_entry["original_text"], original)
        self.assertEqual(test_entry["cleaned_text"], cleaned)
        self.assertEqual(test_entry["robot_score"], score)
        self.assertEqual(test_entry["clichés_found"], cliches)
        
        # 3. Delete entry
        success = database.delete_entry(db_id)
        print(f"Deleted database entry, Success: {success}")
        self.assertTrue(success)
        
        # Check that it's gone
        entries_post = database.get_all_entries()
        deleted_entry = next((e for e in entries_post if e["id"] == db_id), None)
        self.assertIsNone(deleted_entry)

    def test_gemini_api_client(self):
        print("\n--- Testing Gemini API rewrite engine (if key available) ---")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY env variable not set. Skipping active API network call test.")
            return
            
        sample_text = "To whom it may concern, I am a highly motivated team player."
        response = gemini_client.rewrite_cover_letter(sample_text, 25.0, api_key=api_key)
        print("Gemini API Response:")
        print(json.dumps(response, indent=2))
        
        self.assertEqual(response.get("status"), "success")
        self.assertIn("rewritten_output", response)
        self.assertIn("flags", response)
        self.assertTrue(isinstance(response["flags"], list))

if __name__ == "__main__":
    unittest.main()
