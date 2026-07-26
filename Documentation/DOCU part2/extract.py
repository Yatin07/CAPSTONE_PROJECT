
import fitz
import os
import glob
import json

pdf_dir = r"c:\Users\yatin\Downloads\CAP\Documentation\Keep"
pdfs = glob.glob(os.path.join(pdf_dir, "*.pdf"))
results = {}

for pdf in pdfs:
    doc = fitz.open(pdf)
    text = ""
    # Extract first 2 pages and last page
    for i in range(min(2, len(doc))):
        text += doc[i].get_text() + "\n"
    if len(doc) > 2:
        text += doc[-1].get_text() + "\n"
    results[os.path.basename(pdf)] = text

with open("summary.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("Extracted to summary.json")

