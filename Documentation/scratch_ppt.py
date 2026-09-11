import win32com.client
import os
import time

def run():
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    ppt.Visible = True
    
    base_path = os.path.abspath("G1-PPT-Review-I.pptx")
    src_path = os.path.abspath("G1-PPT-Review-I 2 1.pptx")
    
    print(f"Opening {base_path}")
    base_pres = ppt.Presentations.Open(base_path)
    print(f"Opening {src_path}")
    src_pres = ppt.Presentations.Open(src_path)
    
    print("Done opening")
    base_pres.Close()
    src_pres.Close()
    ppt.Quit()

if __name__ == "__main__":
    run()
