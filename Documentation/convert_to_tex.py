import re
import codecs

def md_to_latex(md_text):
    # Escape special latex characters
    # Only escape basic ones to avoid messing up things too much
    latex_text = md_text
    
    # Replace bold and italic
    latex_text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', latex_text)
    latex_text = re.sub(r'\*(.*?)\*', r'\\textit{\1}', latex_text)
    
    lines = latex_text.split('\n')
    latex_lines = []
    
    for line in lines:
        if line.startswith('# '):
            title = line[2:].strip()
            latex_lines.append(f"\\section*{{{title}}}")
        elif line.startswith('## '):
            title = line[3:].strip()
            latex_lines.append(f"\\section{{{title}}}")
        elif line.startswith('### '):
            title = line[4:].strip()
            latex_lines.append(f"\\subsection{{{title}}}")
        elif line.strip() == '---':
            latex_lines.append(r"\vspace{1em}\hrule\vspace{1em}")
        elif line.strip() == '':
            latex_lines.append('')
        else:
            # Escape ampersands and percents if they are not already escaped
            line = line.replace('&', r'\&')
            line = line.replace('%', r'\%')
            latex_lines.append(line)
            
    return '\n'.join(latex_lines)

preamble = r"""\documentclass[12pt, a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\geometry{a4paper, margin=1in}
\usepackage{hyperref}
\usepackage{titlesec}
\usepackage{parskip}
\usepackage{xcolor}

\title{\textbf{LocalDemand: Final Literature Review}}
\author{B.Tech Capstone Project}
\date{\today}

\begin{document}
\maketitle
\tableofcontents
\newpage

"""

with codecs.open('c:/Users/yatin/Downloads/CAP/Documentation/LocalDemand_Final_Literature_Review.md', 'r', 'utf-8') as f:
    md_content = f.read()

latex_body = md_to_latex(md_content)

full_latex = preamble + latex_body + "\n\n\\end{document}\n"

# Fix any potential issues with special characters in titles
full_latex = full_latex.replace(r'\textbf{Author(s) \& Year:}', r'\textbf{Author(s) \& Year:}')
full_latex = full_latex.replace(r'—', r'---') # Em dash for latex

with codecs.open('c:/Users/yatin/Downloads/CAP/Documentation/LocalDemand_Final_Literature_Review.tex', 'w', 'utf-8') as f:
    f.write(full_latex)

print("Successfully converted to LaTeX.")
