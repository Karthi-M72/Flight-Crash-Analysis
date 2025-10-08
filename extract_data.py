"""
Helper: attempt to extract CSV/JSON files from uploaded .zip/.pbit/.pbix files into ./data/
Usage: python extract_data.py
"""
import os, zipfile, shutil, sys
SRC_DIR = "/mnt/data"
OUT_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(OUT_DIR, exist_ok=True)

candidates = [f for f in os.listdir(SRC_DIR) if os.path.isfile(os.path.join(SRC_DIR,f))]
found = []
for fname in candidates:
    fpath = os.path.join(SRC_DIR, fname)
    try:
        if zipfile.is_zipfile(fpath):
            with zipfile.ZipFile(fpath, 'r') as z:
                for info in z.infolist():
                    n = info.filename
                    if n.lower().endswith(('.csv','.json','.txt')):
                        targ = os.path.join(OUT_DIR, os.path.basename(n))
                        with z.open(n) as src, open(targ, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                        print("Extracted", n, "->", targ)
                        found.append(targ)
        else:
            # copy plain CSV/JSON files if present directly in /mnt/data
            if fname.lower().endswith(('.csv','.json','.txt')):
                shutil.copy(os.path.join(SRC_DIR,fname), OUT_DIR)
                print("Copied", fname, "->", OUT_DIR)
                found.append(os.path.join(OUT_DIR,fname))
    except Exception as e:
        print("Error processing", fname, e)
if not found:
    print("No direct CSV/JSON files found in uploads. If your .pbit/.pbix contains the model, extracting programmatically may require Power BI tooling.")
else:
    print("Extraction complete. Files:", found)
