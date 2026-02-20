import os
import csv
import urllib.request

REPO_BASE = "https://raw.githubusercontent.com/lascivaroma/latin-lemmatized-texts/658757de31248993c2e0a3b6eaf51cea48ccb128/"
CORPUS_CSV_URL = REPO_BASE + "corpus.csv"
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'data', 'xml'))

os.makedirs(DATA_DIR, exist_ok=True)

print("Fetching corpus.csv...")
lines = [l.decode('utf-8') for l in urllib.request.urlopen(CORPUS_CSV_URL).readlines()]

vulgate_files = []
for row in csv.DictReader(lines):
    if 'Vulgate' in row['Author'] or 'Genesis' in row['Title']:
        vulgate_files.append((row['Title'], row['File']))

print(f"Found {len(vulgate_files)} Vulgate books. Downloading XML files...")

for title, file_path in vulgate_files:
    file_url = REPO_BASE + file_path
    filename = file_path.split('/')[-1]
    local_path = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(local_path):
        print(f"  Downloading {title} -> {filename}...")
        try:
            urllib.request.urlretrieve(file_url, local_path)
        except Exception as e:
            print(f"  Error downloading {title}: {e}")
    else:
        print(f"  Already have {filename}")

print("Download complete.")
