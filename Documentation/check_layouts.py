import pptx
from pptx import Presentation

prs = Presentation('G1-PPT-Review-I_Merged.pptx')
print(f"Number of slide layouts: {len(prs.slide_layouts)}")
for i, layout in enumerate(prs.slide_layouts):
    print(f"Layout {i}: {layout.name}")
