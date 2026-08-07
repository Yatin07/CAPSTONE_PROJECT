import win32com.client
import os
import time

try:
    source_path = os.path.abspath(r'e:\CAP\RestockIQ_Review-I_MASTER 1 2.pptx')
    template_path = os.path.abspath(r'e:\CAP\Template-Review-I.pptx')
    output_path = os.path.abspath(r'e:\CAP\RestockIQ_Review-I_Final.pptx')

    print("Starting PowerPoint...")
    Application = win32com.client.Dispatch("PowerPoint.Application")
    Application.Visible = True

    print("Opening Source...")
    source_ppt = Application.Presentations.Open(source_path)
    
    print("Opening Template...")
    template_ppt = Application.Presentations.Open(template_path)

    slide_count = source_ppt.Slides.Count
    print(f"Copying {slide_count} slides...")

    for i in range(1, slide_count + 1):
        source_ppt.Slides(i).Copy()
        # Paste at the end
        paste_index = template_ppt.Slides.Count + 1
        pasted_range = template_ppt.Slides.Paste(paste_index)
        
        # Apply the layout / design from the template so it gets the graphics
        pasted_range.Design = template_ppt.Slides(1).Design
        time.sleep(0.5)

    print(f"Saving to {output_path}...")
    template_ppt.SaveAs(output_path)
    
    source_ppt.Close()
    template_ppt.Close()
    Application.Quit()
    print("Merge Complete!")

except Exception as e:
    print("Error during COM automation:", e)
    # Ensure PowerPoint closes if it errors out
    try:
        Application.Quit()
    except:
        pass
