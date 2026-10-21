import win32com.client
import os

def run():
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    
    base_path = os.path.abspath("G1-PPT-Review-I.pptx")
    src_path = os.path.abspath("G1-PPT-Review-I 2 1.pptx")
    out_path = os.path.abspath("G1-PPT-Review-I_Merged.pptx")
    
    if os.path.exists(out_path):
        os.remove(out_path)
        
    print(f"Creating new presentation...")
    pres = ppt.Presentations.Add(True)
    
    print(f"Inserting Base presentation...")
    # Insert all slides from base at index 0 (beginning)
    pres.Slides.InsertFromFile(base_path, 0)
    
    # Delete slide 9 (old Methodology)
    # Note: COM indices are 1-based
    for i in range(1, pres.Slides.Count + 1):
        try:
            title_text = pres.Slides(i).Shapes.Title.TextFrame.TextRange.Text
            if "Proposed Methodology" in title_text:
                print(f"Deleting stale Methodology at slide {i}")
                pres.Slides(i).Delete()
                break
        except:
            pass

    print("Inserting corrected Methodology slide...")
    # Insert slide 6 from src after slide 8
    pres.Slides.InsertFromFile(src_path, 8, 6, 6)
    
    print("Inserting OOA/OOD slides...")
    # Insert slides 7-10 from src after slide 9
    pres.Slides.InsertFromFile(src_path, 9, 7, 10)
    
    # Insert slides 12-15 from src after slide 13 (since we just inserted 4 slides after 9)
    pres.Slides.InsertFromFile(src_path, 13, 12, 15)
    
    print("Fixing ER Diagram (duplicate tables)...")
    for i in range(1, pres.Slides.Count + 1):
        try:
            title_text = pres.Slides(i).Shapes.Title.TextFrame.TextRange.Text
            if "ER Diagram" in title_text:
                print(f"Found ER Diagram at slide {i}")
                er_slide = pres.Slides(i)
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

    # 1. Objectives
    replace_all(pres, "regime-specific tuning for sparse and high-volume items", "3-phase cold-start")
    
    # 2. Scope
    replace_all(pres, "Weather and public-holiday external regressors", "Weather and public-holiday external regressors\n(Gated — Pending Feasibility)")
    replace_all(pres, "Promotion and pricing optimization", "Promotion and pricing optimization\n(except end-of-day waste markdowns)")
    
    # 3. Expected Outcomes
    replace_all(pres, "Adaptive branching expected to hold across both sparse and high-volume items", "3-phase cold-start expected to hold across items")
    replace_all(pres, "Fewer wasted units, fewer stockouts — the downstream effect of a safety-stock-adjusted number", "Fewer wasted units, fewer stockouts — the downstream effect of a safety-stock-adjusted number\nReduced spoilage and waste via price-elastic markdown actions (Waste Action Engine)")
    
    # 4. Feasibility
    replace_all(pres, "adaptive density-based model selection", "3-phase cold-start")
    replace_all(pres, "restock-quantity conversion", "restock-quantity conversion, waste-action markdowns")
    
    # 5. Gantt Chart
    replace_all(pres, "Model Training (Prophet+XGBoost, Adaptive Branching)", "Model Training (Prophet+XGBoost, 3-Phase Cold-Start)")
    replace_all(pres, "Backend API , Restock Logic and LLM narrator", "Backend API, Restock Logic, Waste Engine, and LLM Narrator")
    
    print("Saving merged presentation...")
    pres.SaveAs(out_path)
    
    pres.Close()
    ppt.Quit()
    
    print(f"Successfully saved merged presentation to {out_path}")

if __name__ == "__main__":
    run()
