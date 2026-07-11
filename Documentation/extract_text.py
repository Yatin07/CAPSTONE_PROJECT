import os
import PyPDF2

base_dir = r"c:\Users\yatin\Downloads\CAP"
pdf_files = []
for folder in ["Keep", "Cut"]:
    folder_path = os.path.join(base_dir, folder)
    if os.path.exists(folder_path):
        for f in os.listdir(folder_path):
            if f.endswith(".pdf"):
                pdf_files.append(os.path.join(folder_path, f))

with open(os.path.join(base_dir, "all_papers_text.txt"), "w", encoding="utf-8") as out_f:
    for pdf_path in pdf_files:
        out_f.write(f"\n\n{'='*50}\nFILE: {os.path.basename(pdf_path)}\n{'='*50}\n")
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        out_f.write(text + "\n")
        except Exception as e:
            out_f.write(f"ERROR EXTRACTING TEXT: {e}\n")

print("Done extracting text.")
