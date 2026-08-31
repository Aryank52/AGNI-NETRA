import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('database/ibm_inspection_summary.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for doc in data:
    print('=' * 90)
    print(f"FILE: {doc['filename']}")
    print(f"Total Pages: {doc['total_pages']} | Tables: {len(doc['tables'])}")
    print('=' * 90)
    for t in doc['tables']:
        print(f"Page {t['page']:02d}: {t['title']} | Rows: {t['row_count']} | Headers: {t['headers']}")
