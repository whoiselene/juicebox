# SYSTEM SPECIFICATION DOCUMENT: PROJECT PAPAYA
Component ID: PRJ-PAPAYA-2026
Author: Elene Samsiani
Classification: Architecture & UI Spec

---

## 1. PROJECT VISION & CONTEXT
Project Papaya is an automated desktop companion built to bridge the gap between heavy, high-complexity backend automation and high-fidelity, graphic-forward front-end interfaces. The application targets the sterile nature of modern recruitment tools by actively intercepting corporate jargon in cover letters and transforming them into distinct, narrative-driven career introductions. 

Rather than adopting standard, clinical IDE or enterprise dashboard aesthetics, Papaya relies entirely on a tactile, warm-minimalist, and curvy tropical design language inspired by retro-modern print catalogs.

---

## 2. FRONTEND DESIGN SYSTEM (SPECIFICATION: IMAGE_3A05A1.JPG / IMAGE_3A0625.PNG)

### 2.1 Spatial Geometry & Fluidity
*   **The Curvy Grid:** All sharp, rigid corners are strictly banned. Layout panels, input boxes, buttons, and alert modules must utilize a massive `border-radius` scale ranging between 24px and 36px.
*   **Asymmetric Micro-Layouts:** The core interface splits viewports unevenly—allocating 45% to the soft, tinted input pod and 55% to the crisp, high-contrast rewritten output card to create visual interest.
*   **Tactile Tag Elements:** Identified corporate clichés are rendered as independent, pill-shaped tags (`border-radius: 50px`). These components utilize smooth micro-interactions, scaling upwards (`transform: scale(1.03)`) on mouse hover.

### 2.2 Color Space Mapping (Hexadecimal Constants)
```css
:root {
  --bg-creme:       #F9F6EE; /* Creamy Vanilla base surface */
  --surface-coral:  #D94A43; /* Sunset Coral primary action pods */
  --surface-pink:   #F3B3B7; /* Papaya Pink soft structural divisions */
  --accent-blue:    #9DC3E6; /* Poolside Sky Blue highlight calls */
  --accent-yellow:  #F7D070; /* Mango Yellow metric analytics */
  --text-burgundy:  #5D1F1D; /* Rich Earth Burgundy primary typography */
}
```

*Note: All standard `#000000` pitch-black text and borders are completely replaced by Rich Earth Burgundy to maintain the retro-pop editorial aesthetic.*

---

## 3. CORE SYSTEM ARCHITECTURE

```
  [ NATIVE OS CLIPBOARD ]
             │
      (pyperclip layer)
             ▼
    [ PYTHON BACKGROUND DAEMON ] ──(Spacy / Regex Engine)──> [ JARGON METRICS COLD-RUN ]
             │                                                          │
     (IPC Data Packet)                                                  │
             ▼                                                          ▼
     [ ELECTRON ENGINE ] <─────── [ SQLITE DATABASE ] <─────── [ GEMINI WRAPPER ENGINE ]
   (HTML/CSS/JS Frontend)           (Local Logs & Prompt)          (JSON Parsing Pipeline)
```

### 3.1 The Clipboard Monitor Daemon (Python)

A lightweight background process continuously interfaces with the host operating system's native clipboard pipeline.

* **Trigger Conditions:** The engine polls the clipboard string buffer. The pipeline is activated if the string yields matches for career-specific regex entry-points (e.g., `(?i)(hiring manager|apply for the position|resume enclosed|to whom it may concern)`).
* **Dependencies:** `pyperclip`, `keyboard`, and custom Inter-Process Communication (IPC) hooks to transmit signals to the user interface.

### 3.2 Local NLP Analysis Module (The Cliché Engine)

Prior to network execution, the text is run through a local tokenization filter to compute text density and robotic speech distributions.

* **Dependency Engine:** `spacy` utilizing the optimized `en_core_web_sm` model framework.
* **Mathematical Grading Model:** The local system isolates overused phrases (e.g., *"highly motivated," "results-oriented matrix," "synergistic alignment"*) against a predefined dictionary table, executing the following grading metric:
$$Corporate\ Robot\ Score = \left( \frac{Flagged\ Jargon\ Tokens}{Total\ Text\ Word\ Count} \right) \times 100$$

* **Logic Gate:** If the calculated metric value exceeds 15%, the frontend dynamically fires an amber notification frame using `--accent-yellow`.

### 3.3 Generative Rewrite & AI Pipeline

The text payload, along with context injections, is dispatched asynchronously via HTTPS to the Gemini API endpoint.

* **Prompt Architecture:** System configurations force the LLM backend to extract the hard core engineering metrics of the text while omitting all filler buzzwords.
* **Expected Payload Schema:**

```json
{
  "status": "success",
  "original_score": 42.5,
  "rewritten_output": "String representing clean, narrative-driven text.",
  "flags": [
    {
      "phrase": "results-driven leader",
      "reason": "Devalued phrase. Focus entirely on project metric outputs instead."
    }
  ]
}
```

### 3.4 Data Persistence Layer (SQLite Database Schema)

A secure local SQLite database acts as the archive log, allowing rapid lookups of application history and configuration parameters.

```sql
CREATE TABLE cover_letters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    company_name TEXT NOT NULL,
    original_text TEXT NOT NULL,
    cleaned_text TEXT NOT NULL,
    robot_score REAL NOT NULL,
    clichés_found TEXT 
);

CREATE INDEX idx_company_name ON cover_letters (company_name);
```

---

## 4. PORTFOLIO VALUE PROPOSITION & TECH STACK METRICS

Building Project Papaya showcases advanced technical fluency across distinct software disciplines:

1. **Low-Level Automation & OS Interfacing:** Managing background multi-threading daemons that poll native OS hardware structures safely without resource leaks.
2. **Linguistic Processing & String Math:** Implementing local tokenization, regex lexical analysis, and text parsing pipelines using robust NLP libraries.
3. **Modern UI/UX Fidelity Integration:** Transforming highly complex, programmatic automation pipelines into gorgeous, fluid layouts built exactly to custom UI design constraints (`image_3a05a1.jpg`).
