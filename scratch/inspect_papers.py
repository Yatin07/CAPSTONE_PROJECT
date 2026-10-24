import os
import pypdf

def extract_pdf(path):
    reader = pypdf.PdfReader(path)
    text = ""
    for i, page in enumerate(reader.pages):
        text += f"\n--- PAGE {i+1} ---\n" + page.extract_text()
    return text

# Find Guler
for root, dirs, files in os.walk("Documentation/research-papers"):
    for f in files:
        if "Sensitivity" in f or "Güler" in f or "Guler" in f:
            print("Found Guler:", os.path.join(root, f))
            txt = extract_pdf(os.path.join(root, f))
            with open("scratch/guler_extracted.txt", "w", encoding="utf-8") as out:
                out.write(txt)
        if "Enhanced_sales_forecasting" in f:
            print("Found Lalitha:", os.path.join(root, f))
            txt = extract_pdf(os.path.join(root, f))
            with open("scratch/lalitha_extracted.txt", "w", encoding="utf-8") as out:
                out.write(txt)
