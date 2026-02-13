# Resume–Job Description Matching

## What this project is
This repository contains a Python-based pipeline for matching a resume to job descriptions scraped from Glassdoor.

At a high level, the project:
1. Collects job posting URLs from Glassdoor search results.
2. Scrapes job description details into a dataset (`data.csv`).
3. Converts a resume PDF to plain text.
4. Computes similarity between the resume and each job description, then exports ranked summaries.

The repository also includes generated artifacts such as CSV outputs and visualization images.

## How to run it
I can only provide a **best-known run flow from the scripts in this repo**. Some scripts include old/hardcoded assumptions (for example, Windows geckodriver paths and Python 2 style syntax), so you may need to adapt paths/environment.

### Suggested script order
1. `glassdoor.py` – scrape job listing URLs to `url.json`.
2. `getjd.py` – scrape detailed job info from `url.json` into `data.csv`.
3. `step2_getresume.py` – extract text from a resume PDF into `resumeconverted.txt`.
4. `Doc_Similarity.py` **or** `step3_model_buidling.py` – compute similarity/ranking outputs.

### Notes and constraints discovered from code
- The scraping scripts use Selenium + Firefox and currently hardcode a Windows geckodriver path (`C:\Tools\...\geckodriver.exe`).
- The resume extraction script expects a file named `Binoy_Dutt_Resume.pdf` in the project directory.
- Several scripts use Python 2 constructs (`print` statements without parentheses, `cStringIO`, `string.maketrans`, etc.).
- Because of the above, this project appears to have been authored for an older Python environment and may require modernization for Python 3.

### Minimal run commands (if your environment is compatible)
```bash
python glassdoor.py
python getjd.py
python step2_getresume.py
python Doc_Similarity.py
# or
python step3_model_buidling.py
```



## No-scraping mode
Use this mode when you already have job descriptions in `data.csv` and want matching only (no Selenium scraping).

### 1) Install dependencies
```bash
pip install -r requirements.txt
```

### 2) Prepare resume text
Create a plain-text resume file at `private/resume.txt` (or pass any path with `--resume`).

### 3) Run matcher
```bash
python match_no_scrape.py --resume private/resume.txt --data data.csv
```

This writes `ranked_matches.csv` and prints the top 5 matches to stdout.


## How to run tests
I could not find an automated test suite (no test files, test runner config, or CI config in this repository).

So, test execution is currently **unknown/not defined** from the repository contents. A practical validation approach is to run the pipeline scripts and inspect generated outputs (`data.csv`, `Summary.csv`, `Summaryimproved.csv`, and distance plots).
