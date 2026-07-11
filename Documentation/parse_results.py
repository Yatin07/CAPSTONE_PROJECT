import re
import json
import os

def process_file(text, filename):
    result = {
        'Dataset': 'Not found in text.',
        'Method': 'Not found in text.',
        'Result': 'Not found in text.',
        'Quote': 'Not found in text.'
    }
    
    # Dataset
    dataset_m = re.search(r'((?:we|the|our)\s+(?:dataset|data)\s+(?:contains|has|includes|from).*?\.)', text, re.IGNORECASE)
    if dataset_m: result['Dataset'] = dataset_m.group(1).replace('\n', ' ').strip()
    else:
        dataset_m = re.search(r'(.{0,30}(?:dataset|data|collected|records).{0,50})', text, re.IGNORECASE)
        if dataset_m: result['Dataset'] = dataset_m.group(1).replace('\n', ' ').strip()

    # Method
    method_m = re.search(r'(.{0,30}(?:Prophet|LSTM|ARIMA|SARIMA|method|model|approach).{0,50})', text, re.IGNORECASE)
    if method_m: result['Method'] = method_m.group(1).replace('\n', ' ').strip()
        
    # Result
    res_m = re.search(r'(.{0,30}(?:MAE|RMSE|MAPE|accuracy|error|R2|R\^2)\s+(?:is|of|=)\s+[\d\.]+.{0,30})', text, re.IGNORECASE)
    if res_m: result['Result'] = res_m.group(1).replace('\n', ' ').strip()
    else:
        res_m = re.search(r'(.{0,30}(?:MAE|RMSE|MAPE|accuracy).{0,30})', text, re.IGNORECASE)
        if res_m: result['Result'] = res_m.group(1).replace('\n', ' ').strip()
        
    # Quote
    quote_m = re.search(r'Conclusion.*?\n(.*?)\.', text, re.IGNORECASE | re.DOTALL)
    if quote_m:
        words = quote_m.group(1).split()
        if len(words) <= 20:
            result['Quote'] = " ".join(words)
        else:
            result['Quote'] = " ".join(words[:19]) + "."
    else:
        # Just grab any sentence with less than 20 words
        sentences = re.findall(r'(\b[A-Z][^\.]{20,100}\.)', text)
        for s in sentences:
            w = s.split()
            if 8 < len(w) <= 20:
                result['Quote'] = s.replace('\n', ' ')
                break

    return result

base_dir = r"c:\Users\yatin\Downloads\CAP"
with open(os.path.join(base_dir, 'all_papers_text.txt'), 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

papers = content.split('==================================================')
output = {}
for i in range(1, len(papers)-1, 2):
    filename = papers[i].replace('FILE:', '').strip()
    text = papers[i+1]
    if len(text.strip()) < 100:
        output[filename] = "COULD NOT VERIFY"
    else:
        output[filename] = process_file(text, filename)

with open(os.path.join(base_dir, 'extraction_results.json'), 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=4)
print("JSON written.")
