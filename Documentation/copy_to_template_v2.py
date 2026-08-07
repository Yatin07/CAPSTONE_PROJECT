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
    
    print("Opening Template...")
    template_ppt = Application.Presentations.Open(template_path)

    initial_slide_count = template_ppt.Slides.Count
    print(f"Template initially has {initial_slide_count} slides.")

    print(f"Inserting slides from {source_path}...")
    # Insert all slides from the source presentation at the end of the template
    template_ppt.Slides.InsertFromFile(source_path, initial_slide_count)

    print("Applying template graphics and ratio to all inserted slides...")
    # Get the design (aspect ratio, graphics, colors) of the template
    template_design = template_ppt.Slides(1).Design
    
    # Apply it to all slides
    for slide in template_ppt.Slides:
        slide.Design = template_design
        
    # We delete the original template slides (assuming there were 1 or 2 sample slides at the start)
    # We delete backwards to not mess up indexes
    if initial_slide_count > 0:
        for i in range(initial_slide_count, 0, -1):
            template_ppt.Slides(i).Delete()

    print(f"Saving to {output_path}...")
    template_ppt.SaveAs(output_path)
    
    template_ppt.Close()
    Application.Quit()
    print("Merge Complete! All slides now have the template graphics.")

except Exception as e:
    print("Error during COM automation:", e)
    try:
        Application.Quit()
    except:
        pass
