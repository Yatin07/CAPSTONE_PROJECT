import win32com.client
import os

def run():
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    
    base_path = os.path.abspath("G1-PPT-Review-I.pptx")
    out_path = os.path.abspath("G2-PPT-Review-II-Final.pptx")
    
    if os.path.exists(out_path):
        os.remove(out_path)
        
    print("Opening base presentation...")
    pres = ppt.Presentations.Open(base_path, WithWindow=False)
    
    print("Saving as new file...")
    pres.SaveAs(out_path)
    
    print("Deleting all slides except Slide 2...")
    total_slides = pres.Slides.Count
    for i in range(total_slides, 0, -1):
        if i != 2:
            pres.Slides(i).Delete()
            
    # Now pres has exactly 1 slide. Let's duplicate it twice to have 3 slides.
    print("Duplicating slides...")
    slide1 = pres.Slides(1)
    slide2_range = slide1.Duplicate()
    slide2 = pres.Slides(2)
    slide3_range = slide1.Duplicate()
    slide3 = pres.Slides(3)
    
    def replace_slide_content(slide, new_title, new_body):
        for shape in slide.Shapes:
            if shape.HasTextFrame:
                text = shape.TextFrame.TextRange.Text
                if text.strip() == "Outline":
                    shape.TextFrame.TextRange.Text = new_title
                elif "Introduction" in text and "Problem Statement" in text:
                    shape.TextFrame.TextRange.Text = new_body
                    
    print("Setting content for Slide 1...")
    body1 = (
        "• Machine Learning Grid Search is fully built and running (bakery_model.py).\n"
        "• Cross-Validation pipeline is active and calculating baseline RMSE metrics.\n"
        "• Flutter 'Warm Tech' UI is successfully scaffolded via Stitch MCP.\n"
        "• FastAPI bridge architecture is finalized and ready for ML integration."
    )
    replace_slide_content(slide1, "Implementation Progress (>50% Completed)", body1)
    
    print("Setting content for Slide 2...")
    body2 = (
        "[ PLEASE PASTE YOUR SCREENSHOTS HERE ]\n\n"
        "1. Screenshot of Python terminal showing Prophet Grid Search and RMSE output.\n\n"
        "2. Screenshot of Flutter mobile app UI (Dashboard)."
    )
    replace_slide_content(slide2, "Working Demonstration & Initial Results", body2)
    
    print("Setting content for Slide 3...")
    body3 = (
        "GANTT CHART PROGRESS:\n"
        "• Project is strictly on schedule per the Review 1 timeline.\n\n"
        "KEY CHALLENGES OVERCOME:\n"
        "• Addressed SME data sparsity via XGBoost hybrid.\n"
        "• Bypassed weather API rate limits using data caching.\n\n"
        "REMAINING WORK (Review 3):\n"
        "• FastAPI integration, Waste Action Engine intraday logic, and Indian holdout dataset testing.\n\n"
        "FUTURE EXTENSIONS (Beyond Scope):\n"
        "• Multi-location chain forecasting, live POS hardware integration, and interactive LLM chatbot."
    )
    replace_slide_content(slide3, "Project Status, Remaining Work & Future Extensions", body3)
    
    print("Saving and closing...")
    pres.Save()
    pres.Close()
    
    # Do not Quit ppt application to avoid affecting other open presentations, but since we are running in background, it's fine.
    # We will just leave it open or let COM release it.
    print(f"Successfully created {out_path}")

if __name__ == "__main__":
    run()
