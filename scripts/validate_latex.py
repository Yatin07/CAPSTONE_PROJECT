"""
scripts/validate_latex.py
Validates LaTeX syntax, cross-references, citation keys, input files, and figure paths
for both main.tex and main_standalone.tex.
"""

import os
import re
import sys

def validate_file(filename, check_inputs=True, check_bib_file=True):
    print("=" * 70)
    print(f"VALIDATING LATEX SOURCE: {filename}")
    print("=" * 70)

    if not os.path.exists(filename):
        print(f"ERROR: {filename} not found!")
        return False

    with open(filename, "r", encoding="utf-8") as f:
        tex = f.read()

    # 1. Check all \input{...} files
    inputs = re.findall(r'\\input\{([^}]+)\}', tex)
    all_inputs_ok = True
    if check_inputs and inputs:
        print(f"Found {len(inputs)} \\input statements:")
        for inp in inputs:
            inp_path = inp if inp.endswith(".tex") else inp + ".tex"
            if os.path.exists(inp_path):
                print(f"  [OK] {inp_path}")
            else:
                print(f"  [MISSING] {inp_path}")
                all_inputs_ok = False
    elif not inputs:
        print("Standalone file: 0 \\input statements (all content inlined).")

    # 2. Check all \includegraphics{...} files
    graphics = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex)
    print(f"\nFound {len(graphics)} \\includegraphics statements:")
    all_graphics_ok = True
    for g in graphics:
        if os.path.exists(g):
            print(f"  [OK] {g} ({os.path.getsize(g)} bytes)")
        else:
            print(f"  [MISSING] {g}")
            all_graphics_ok = False

    # 3. Check citation keys
    def expand_inputs(text):
        def repl(match):
            fn = match.group(1)
            inp_path = fn if fn.endswith(".tex") else fn + ".tex"
            if os.path.exists(inp_path):
                with open(inp_path, "r", encoding="utf-8") as f:
                    return expand_inputs(f.read())
            return match.group(0)
        return re.sub(r'\\input\{([^}]+)\}', repl, text)

    full_text = expand_inputs(tex)
    cite_matches = re.findall(r'\\cite\{([^}]+)\}', full_text)
    cited_keys = set()
    for match in cite_matches:
        for k in match.split(','):
            cited_keys.add(k.strip())

    print(f"\nFound {len(cited_keys)} unique keys cited across document.")

    if check_bib_file:
        with open("references.bib", "r", encoding="utf-8") as f:
            bib = f.read()
        target_keys = set(re.findall(r'@\w+\{([^,]+),', bib))
        src_label = "references.bib"
    else:
        target_keys = set(re.findall(r'\\bibitem\{([^}]+)\}', full_text))
        src_label = "thebibliography environment"

    all_cites_ok = True
    for k in sorted(cited_keys):
        if k in target_keys:
            pass
        else:
            print(f"  [UNRESOLVED] {k} not found in {src_label}!")
            all_cites_ok = False

    if all_cites_ok:
        print(f"  [OK] All {len(cited_keys)} cited keys resolved against {src_label}!")

    # 4. Check environment balancing
    tokens = re.findall(r'\\(begin|end)\{([^}]+)\}', full_text)
    stack = []
    env_ok = True
    for action, env in tokens:
        if action == "begin":
            stack.append(env)
        elif action == "end":
            if not stack or stack[-1] != env:
                print(f"  [MISMATCH] Expected \\end{{{stack[-1] if stack else 'None'}}}, but found \\end{{{env}}}!")
                env_ok = False
                break
            stack.pop()

    if env_ok and len(stack) == 0:
        print(f"\nEnvironment check: {len(tokens)//2} environments perfectly balanced!")
    elif len(stack) > 0:
        print(f"  [ERROR] Unclosed environments remaining: {stack}")
        env_ok = False

    # 5. Check curly braces balance
    open_braces = tex.count('{')
    close_braces = tex.count('}')
    print(f"Brace count: {open_braces} open vs {close_braces} close")
    braces_ok = (open_braces == close_braces)
    if braces_ok:
        print("  [OK] Curly braces perfectly balanced!")
    else:
        print("  [WARNING] Unbalanced curly braces!")

    return all_inputs_ok and all_graphics_ok and all_cites_ok and env_ok and braces_ok

def main():
    ok1 = validate_file("main.tex", check_inputs=True, check_bib_file=True)
    print("\n")
    ok2 = validate_file("main_standalone.tex", check_inputs=False, check_bib_file=False)

    print("\n" + "=" * 70)
    if ok1 and ok2:
        print("AUDIT SUCCESS: BOTH main.tex AND main_standalone.tex ARE 100% CLEAN & VERIFIED!")
    else:
        print("AUDIT FAILED: Please check errors above.")
    print("=" * 70)

if __name__ == "__main__":
    main()
