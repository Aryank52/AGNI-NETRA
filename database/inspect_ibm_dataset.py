"""
AGNI-NETRA — Inspect and Prepare all IBM Mining Datasets
Analyzes all PDF files present under IBM directory, extracts metadata,
table structures, document classifications, and data limitations.
"""

import os
import sys
import json
import pdfplumber

def main():
    ibm_dir = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FACILITIES\IBM"
    pdf_files = [f for f in os.listdir(ibm_dir) if f.endswith(".pdf")]
    
    print("=" * 100)
    print(f"AGNI-NETRA — IBM MINING DATASET INSPECTION & CLASSIFICATION")
    print(f"Directory: {ibm_dir}")
    print(f"Total PDFs Detected: {len(pdf_files)}")
    print("=" * 100)
    
    doc_reports = []

    for fname in sorted(pdf_files):
        fpath = os.path.join(ibm_dir, fname)
        fsize = os.path.getsize(fpath)
        
        with pdfplumber.open(fpath) as pdf:
            total_pages = len(pdf.pages)
            meta = pdf.metadata or {}
            
            # Extract first 5 pages text to detect title, publisher, reference dates
            first_pages_text = "\n".join([pdf.pages[i].extract_text() or "" for i in range(min(5, total_pages))])
            
            # Detect Table inventory across all pages
            table_inventory = []
            has_coords = False
            has_state_district = False
            has_mineral = False
            has_lease = False
            
            for p_idx, page in enumerate(pdf.pages):
                p_num = p_idx + 1
                p_text = page.extract_text() or ""
                
                # Check keywords
                if any(k in p_text.lower() for k in ["latitude", "longitude", "deg min sec", "coordinates"]):
                    has_coords = True
                if any(k in p_text.lower() for k in ["district", "state"]):
                    has_state_district = True
                if any(k in p_text.lower() for k in ["bauxite", "iron ore", "limestone", "coal", "copper", "manganese", "chromite"]):
                    has_mineral = True
                if any(k in p_text.lower() for k in ["mining lease", "leases", "ml area", "pl area", "prospecting licence"]):
                    has_lease = True
                
                # Extract tables
                raw_tables = page.extract_tables()
                if raw_tables:
                    # Find table title from text above the table
                    lines = [l.strip() for l in p_text.split("\n") if l.strip()]
                    tbl_lines = [l for l in lines if l.lower().startswith("table") or "table no" in l.lower() or "statement" in l.lower() or "annexure" in l.lower()]
                    tbl_title = tbl_lines[0] if tbl_lines else f"Table on Page {p_num}"
                    
                    for t_idx, tbl in enumerate(raw_tables):
                        headers = [str(c).replace("\n", " ").strip() for c in tbl[0] if c is not None] if tbl else []
                        num_rows = len(tbl) - 1 if len(tbl) > 1 else 0
                        table_inventory.append({
                            "page": p_num,
                            "table_index": t_idx + 1,
                            "title": tbl_title,
                            "headers": headers[:8],
                            "row_count": num_rows,
                            "sample_row": [str(c).replace("\n", " ").strip() for c in tbl[1][:6]] if len(tbl) > 1 else []
                        })

        doc_reports.append({
            "filename": fname,
            "size_bytes": fsize,
            "size_mb": round(fsize / (1024 * 1024), 3),
            "total_pages": total_pages,
            "metadata": meta,
            "first_text_snippet": first_pages_text[:1200],
            "has_coordinates": has_coords,
            "has_state_district": has_state_district,
            "has_mineral": has_mineral,
            "has_lease": has_lease,
            "tables": table_inventory
        })

    # Save detailed analysis JSON
    out_json_path = os.path.join(r"E:\PROJECTS\AGNI-NETRA\database", "ibm_inspection_summary.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(doc_reports, f, indent=2)
    print(f"\n[OK] Inspection JSON report saved to: {out_json_path}")
    
    # Print human-readable summary
    for doc in doc_reports:
        print("\n" + "#" * 90)
        print(f"DOCUMENT: {doc['filename']}")
        print(f"Size: {doc['size_mb']} MB ({doc['size_bytes']:,} bytes) | Total Pages: {doc['total_pages']}")
        print(f"Metadata: {doc['metadata']}")
        print(f"Content Flags: Coordinates={doc['has_coordinates']}, State/District={doc['has_state_district']}, Mineral={doc['has_mineral']}, Lease={doc['has_lease']}")
        print(f"Total Tables Detected: {len(doc['tables'])}")
        print("-" * 90)
        print("SAMPLE TEXT / HEADERS:")
        print(doc['first_text_snippet'][:600])
        print("-" * 90)
        print("TABLE INVENTORY SAMPLE:")
        for t in doc['tables'][:15]:
            print(f"  [Page {t['page']:02d}] {t['title']} | Rows: {t['row_count']} | Headers: {t['headers']}")

if __name__ == "__main__":
    main()
