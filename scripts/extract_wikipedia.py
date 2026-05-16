"""
Extract Wikipedia articles from Kaggle SQLite database to individual .txt files.

Legacy optional dataset for the original hackathon benchmark (default app uses data/medical).

Usage: python scripts/extract_wikipedia.py

Expects SQLite DB at ./data/raw/articles.db
Outputs .txt files to ./data/wikipedia/
"""

import os
import sqlite3


def extract_articles(
    db_path: str = "./data/raw/articles.db",
    output_dir: str = "./data/wikipedia",
    limit: int = 5000,
):
    """
    Extract articles from SQLite and write each as a .txt file.

    Args:
        db_path: Path to the Kaggle SQLite database.
        output_dir: Directory to write .txt article files.
        limit: Max number of articles to extract.
    """
    os.makedirs(output_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT title, text FROM articles LIMIT {limit}")

    count = 0
    for i, (title, text) in enumerate(cursor.fetchall()):
        filename = os.path.join(output_dir, f"article_{i:05d}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{text}")
        count += 1

    conn.close()
    print(f"✅ Extracted {count} articles to {output_dir}/")


if __name__ == "__main__":
    extract_articles()
