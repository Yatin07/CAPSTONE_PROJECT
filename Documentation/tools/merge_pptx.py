import win32com.client
import os

def run():
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    
    base_path = os.path.abspath("G1-PPT-Review-I.pptx")
    src_path = os.path.abspath("G1-PPT-Review-I 2 1.pptx")
    out_path = os.path.abspath("G1-PPT-Review-I_Merged.pptx")
    
    if os.path.exists(out_path):
        os.remove(out_path)
        
    print(f"Opening {base_path}")
    base_pres = ppt.Presentations.Open(base_path)
    print(f"Opening {src_path}")
    src_pres = ppt.Presentations.Open(src_path)
    
    # Let's find Methodology slide in Base and delete it
    for i in range(1, base_pres.Slides.Count + 1):
        try:
            # find slide with "Proposed Methodology" title
            if "Proposed Methodology" in base_pres.Slides(i).Shapes.Title.TextFrame.TextRange.Text:
                base_pres.Slides(i).Delete()
                break
        except:
            pass

    # Copy Slide 6 from Src
    src_pres.Slides(6).Copy()
    base_pres.Slides.Paste(Index=9)
    
    print("Copying OOA/OOD slides...")
    # Paste OOA/OOD starting at index 10
    insert_index = 10
    for src_idx in [7, 8, 9, 10, 12, 13, 14, 15]:
        src_pres.Slides(src_idx).Copy()
        base_pres.Slides.Paste(Index=insert_index)
        insert_index += 1
        
    print(f"Total slides after paste: {base_pres.Slides.Count}")
    
    # Dynamically find the ER Diagram slide (has "ER Diagram" in title)
    for i in range(1, base_pres.Slides.Count + 1):
        try:
            title_text = base_pres.Slides(i).Shapes.Title.TextFrame.TextRange.Text
            if "ER Diagram" in title_text:
                print(f"Found ER Diagram at slide {i}")
                er_slide = base_pres.Slides(i)
                tables_seen = {}
                shapes_to_delete = []
                for shape in er_slide.Shapes:
                    if shape.HasTable:
                        try:
                            first_cell_text = shape.Table.Cell(1, 1).Shape.TextFrame.TextRange.Text.strip()
                            if first_cell_text in ["WEATHER", "INVENTORY", "FORECAST"]:
                                if first_cell_text in tables_seen:
                                    shapes_to_delete.append(shape)
                                else:
                                    tables_seen[first_cell_text] = True
                        except:
                            pass
                for shape in shapes_to_delete:
                    shape.Delete()
                break
        except:
            pass
            
    print("Applying text replacements globally...")
    def replace_all(pres, old_t, new_t):
        for i in range(1, pres.Slides.Count + 1):
            slide = pres.Slides(i)
            for shape in slide.Shapes:
                if shape.HasTextFrame:
                    tr = shape.TextFrame.TextRange
                    if old_t in tr.Text:
                        tr.Text = tr.Text.replace(old_t, new_t)
                if shape.HasTable:
                    for row in range(1, shape.Table.Rows.Count + 1):
                        for col in range(1, shape.Table.Columns.Count + 1):
                            cell = shape.Table.Cell(row, col)
                            if cell.Shape.HasTextFrame:
                                tr = cell.Shape.TextFrame.TextRange
                                if old_t in tr.Text:
                                    tr.Text = tr.Text.replace(old_t, new_t)

    # Apply globally
    replace_all(base_pres, "regime-specific tuning for sparse and high-volume items", "3-phase cold-start")
    replace_all(base_pres, "Weather and public-holiday external regressors", "Weather and public-holiday external regressors\n(Gated — Pending Feasibility)")
    replace_all(base_pres, "Promotion and pricing optimization", "Promotion and pricing optimization\n(except end-of-day waste markdowns)")
    replace_all(base_pres, "Adaptive branching expected to hold across both sparse and high-volume items", "3-phase cold-start expected to hold across items")
    
    replace_all(base_pres, "Fewer wasted units, fewer stockouts — the downstream effect of a safety-stock-adjusted number", "Fewer wasted units, fewer stockouts — the downstream effect of a safety-stock-adjusted number\nReduced spoilage and waste via price-elastic markdown actions (Waste Action Engine)")
    
    replace_all(base_pres, "adaptive density-based model selection", "3-phase cold-start")
    replace_all(base_pres, "restock-quantity conversion", "restock-quantity conversion, waste-action markdowns")
    replace_all(base_pres, "Model Training (Prophet+XGBoost, Adaptive Branching)", "Model Training (Prophet+XGBoost, 3-Phase Cold-Start)")
    replace_all(base_pres, "Backend API , Restock Logic and LLM narrator", "Backend API, Restock Logic, Waste Engine, and LLM Narrator")
    
    print("Saving merged presentation...")
    base_pres.SaveAs(out_path)
    
    base_pres.Close()
    src_pres.Close()
    ppt.Quit()
    
    print(f"Successfully saved merged presentation to {out_path}")

if __name__ == "__main__":
    run()
