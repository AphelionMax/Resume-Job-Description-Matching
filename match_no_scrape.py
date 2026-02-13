"""No-scraping resume/job matcher.

Purpose:
- Load resume text from a local file.
- Load job descriptions from an existing CSV file.
- Rank jobs by TF-IDF cosine similarity against the resume.

This script is intentionally standalone so you can run matching without using the
legacy scraping scripts.
"""

import argparse
import re
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Function: parse CLI arguments
# What: Defines user-facing options for resume/data/output paths.
# Why: Keeping this isolated makes the script easier to test/extend.
# Gotcha: argparse returns strings, so path validation is handled later.
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank job descriptions against a resume (no scraping).")
    parser.add_argument("--resume", default="private/resume.txt", help="Path to plain-text resume file.")
    parser.add_argument("--data", default="data.csv", help="Path to CSV with job descriptions.")
    parser.add_argument("--output", default="ranked_matches.csv", help="Path for ranked CSV output.")
    return parser.parse_args()


# Function: normalize text safely
# What: Converts values to compact strings with normalized whitespace.
# Why: Input CSV cells may contain NaN/non-string values; this avoids TF-IDF errors.
# Tip: This style is safer than doing str(value) directly on NaN because it avoids "nan" noise.
def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    return re.sub(r"\s+", " ", text).strip()


# Function: choose best description column
# What: Detects likely job description column by name+content heuristics.
# Why: Real-world CSV headers vary (e.g., "Job Description", "description", "details").
# Gotcha: If two columns tie on names, longer text averages often indicate real descriptions.
def detect_description_column(df: pd.DataFrame) -> str:
    keyword_weights = {
        "job description": 6,
        "description": 5,
        "responsibilities": 4,
        "details": 3,
        "summary": 2,
        "text": 1,
    }

    best_col = None
    best_score = float("-inf")

    for col in df.columns:
        col_name = col.lower().strip()
        name_score = sum(weight for key, weight in keyword_weights.items() if key in col_name)

        series = df[col].map(clean_text)
        non_empty = series[series != ""]
        avg_len = non_empty.map(len).mean() if not non_empty.empty else 0

        total_score = name_score * 1000 + avg_len
        if total_score > best_score:
            best_score = total_score
            best_col = col

    if best_col is None:
        raise ValueError("Could not detect a description-like column in the CSV.")
    return best_col


# Function: pick optional metadata columns (title/company/url)
# What: Finds likely columns for display in output if they exist.
# Why: Different datasets use different headers; flexible detection avoids hardcoding.
def detect_optional_columns(df: pd.DataFrame) -> dict:
    column_map = {"title": None, "company": None, "url": None}
    lower_lookup = {c.lower().strip(): c for c in df.columns}

    candidate_names = {
        "title": ["title", "position", "job title", "role"],
        "company": ["company", "employer", "organization"],
        "url": ["url", "link", "job_url", "posting_url"],
    }

    for key, names in candidate_names.items():
        for name in names:
            if name in lower_lookup:
                column_map[key] = lower_lookup[name]
                break

    return column_map


# Function: rank jobs by similarity
# What: Builds TF-IDF vectors and computes cosine similarity scores.
# Why: TF-IDF + cosine is a strong baseline for text matching and easy to explain.
# Gotcha: Empty description rows are filtered to prevent misleading zero-text matches.
def rank_matches(resume_text: str, df: pd.DataFrame, description_col: str) -> pd.DataFrame:
    work_df = df.copy()
    work_df["_description"] = work_df[description_col].map(clean_text)
    work_df = work_df[work_df["_description"] != ""].copy()

    if work_df.empty:
        raise ValueError("No non-empty job descriptions found in the selected column.")

    corpus = [resume_text] + work_df["_description"].tolist()

    # Tip: stop_words='english' reduces noisy words (the, and, with) for clearer matching.
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    resume_vector = tfidf_matrix[0:1]
    job_vectors = tfidf_matrix[1:]
    scores = cosine_similarity(resume_vector, job_vectors).flatten()

    work_df["score"] = scores
    return work_df.sort_values("score", ascending=False).reset_index(drop=True)


# Function: build final output table
# What: Creates the exact output schema required by this task.
# Why: Keeping this separate clarifies formatting and export logic.
def build_output_table(ranked_df: pd.DataFrame, optional_cols: dict) -> pd.DataFrame:
    output_rows = []

    for idx, row in ranked_df.iterrows():
        description = clean_text(row["_description"])
        snippet = description[:220] + ("..." if len(description) > 220 else "")

        output_rows.append(
            {
                "rank": idx + 1,
                "score": round(float(row["score"]), 6),
                "title": clean_text(row[optional_cols["title"]]) if optional_cols["title"] else "",
                "company": clean_text(row[optional_cols["company"]]) if optional_cols["company"] else "",
                "url": clean_text(row[optional_cols["url"]]) if optional_cols["url"] else "",
                "snippet": snippet,
            }
        )

    return pd.DataFrame(output_rows, columns=["rank", "score", "title", "company", "url", "snippet"])


# Main execution block
# What: Orchestrates file loading, matching, CSV export, and console preview.
# Why: A linear flow here keeps the script beginner-friendly and debuggable.
# Gotcha: Resume file must contain plain text (UTF-8 recommended).
def main() -> None:
    args = parse_args()

    resume_path = Path(args.resume)
    data_path = Path(args.data)

    if not resume_path.exists():
        raise FileNotFoundError(f"Resume file not found: {resume_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Data CSV not found: {data_path}")

    resume_text = clean_text(resume_path.read_text(encoding="utf-8"))
    if not resume_text:
        raise ValueError("Resume text is empty. Please provide content in the --resume file.")

    df = pd.read_csv(data_path)
    description_col = detect_description_column(df)
    optional_cols = detect_optional_columns(df)

    ranked = rank_matches(resume_text, df, description_col)
    output_df = build_output_table(ranked, optional_cols)
    output_df.to_csv(args.output, index=False)

    print(f"Detected description column: {description_col}")
    print(f"Wrote ranked matches: {args.output}")
    print("Top 5 matches:")

    preview = output_df.head(5)
    for _, item in preview.iterrows():
        print(
            f"#{int(item['rank'])} | score={item['score']:.6f} | "
            f"title={item['title']} | company={item['company']} | url={item['url']}"
        )


if __name__ == "__main__":
    main()
