# Pipeline walkthrough (inputs → scripts → outputs)

This document explains the intended end-to-end flow in this repository.

## Stage 1: Discover job posting URLs

- **Input**: search parameters in `glassdoor.py` (`locid`, `key`).
- **Script**: `glassdoor.py`.
- **What it does**:
  - Launches Firefox through Selenium.
  - Opens Glassdoor search results.
  - Iterates pagination and collects posting links (`li.jl > a`).
- **Output**: `url.json` (list of job post URLs).

## Stage 2: Scrape job description details

- **Input**: `url.json` produced by Stage 1.
- **Script**: `getjd.py`.
- **What it does**:
  - Opens each URL with Selenium.
  - Parses company, position, location, metadata, and full job description with BeautifulSoup.
  - Appends each posting as one record.
- **Output**: `data.csv` (tabular dataset of postings + descriptions).

## Stage 3: Convert resume PDF to plain text

- **Input**: a PDF resume (`Binoy_Dutt_Resume.pdf`, hardcoded in script).
- **Script**: `step2_getresume.py`.
- **What it does**:
  - Uses pdfminer to extract text page-by-page.
- **Output**: `resumeconverted.txt`.

## Stage 4A: Baseline similarity/ranking path

- **Inputs**: `data.csv` + `resumeconverted.txt`.
- **Script**: `Doc_Similarity.py`.
- **What it does**:
  - Trains a Doc2Vec model on job descriptions.
  - Infers a vector for the resume.
  - Computes cosine distance between resume and each job posting.
  - Extracts per-job keywords.
  - Creates an MDS plot of document distances.
- **Outputs**:
  - `Summary.csv` (ranked result table).
  - `distance.png` (MDS visualization).

## Stage 4B: “Improved” similarity/ranking path (alternative)

- **Inputs**: `data.csv` + `resumeconverted.txt` + GoogleNews word2vec binary (external path hardcoded in script).
- **Script**: `step3_model_buidling.py`.
- **What it does**:
  - Builds custom TF-IDF weights over all job descriptions + resume.
  - Looks up word vectors for tokens.
  - Produces weighted mean vectors per document.
  - Computes cosine distance to the resume vector.
  - Builds MDS and PCA visualizations.
  - Extracts stemmed keywords.
- **Outputs**:
  - `Summaryimproved.csv`.
  - `distance_MDS_improved.png`.
  - `distance_PCA_improved.png`.

## One-line run order

1. `python glassdoor.py`
2. `python getjd.py`
3. `python step2_getresume.py`
4. `python Doc_Similarity.py` **or** `python step3_model_buidling.py`

## Files that are pipeline artifacts already present in this repository

- URL/data intermediates: `url.json`, `data.csv`.
- Ranking outputs: `Summary.csv`, `Summaryimproved.csv`.
- Visual outputs: `distance.png`, `distance_MDS.png`, `distance_PCA.png`, `distance_MDS_improved.png`, `distance_PCA_improved.png`.
- Other data-like artifacts in repo root: `matrix.json`, `topic_list.json`.
