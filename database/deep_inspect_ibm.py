import pdfplumber
import sys

sys.stdout.reconfigure(encoding='utf-8')

def deep_inspect_nmi():
    fpath = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FACILITIES\IBM\11122022113003Res_All India Summary_2020.pdf"
    print("=" * 80)
    print("NMI AT A GLANCE - 2020 (PROVISIONAL)")
    print("=" * 80)
    with pdfplumber.open(fpath) as pdf:
        for idx, p in enumerate(pdf.pages):
            text = p.extract_text()
            print(f"--- Page {idx+1} ---")
            print(text[:800])

def deep_inspect_ml_bulletin():
    fpath = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FACILITIES\IBM\1763377395691b00f36d15cML_PL_2024.pdf"
    print("\n" + "=" * 80)
    print("MINING LEASE BULLETIN - 2024 (PROVISIONAL)")
    print("=" * 80)
    with pdfplumber.open(fpath) as pdf:
        # Table 1: Page 12
        print("\n--- Table 1 (Page 12): State-wise Summary ---")
        print(pdf.pages[11].extract_text()[:600])
        
        # Table 2: Page 14
        print("\n--- Table 2 (Page 14): Mineral-wise Summary ---")
        print(pdf.pages[13].extract_text()[:600])
        
        # Table 3: Page 15
        print("\n--- Table 3 (Page 15): State-wise / District-wise / Mineral-wise ---")
        print(pdf.pages[14].extract_text()[:600])
        
        # Table 4 & 5: Page 30
        print("\n--- Table 4 & 5 (Page 30): High & Medium Potential Districts ---")
        print(pdf.pages[29].extract_text()[:800])
        
        # Table 6: Page 31
        print("\n--- Table 6 (Page 31): Low Mineral Potential Districts ---")
        print(pdf.pages[30].extract_text()[:800])
        
        # Table 8: Page 35
        print("\n--- Table 8 (Page 35): Sector-wise (Public vs Private) ---")
        print(pdf.pages[34].extract_text()[:600])
        
        # Table 9: Page 40
        print("\n--- Table 9 (Page 40): Public Sector Leases ---")
        print(pdf.pages[39].extract_text()[:600])
        
        # Table 12: Page 46
        print("\n--- Table 12 (Page 46): Auction Summary ---")
        print(pdf.pages[45].extract_text()[:600])
        
        # Table 15: Page 53
        print("\n--- Table 15 (Page 53): Successful Auctions 2024-25 ---")
        print(pdf.pages[52].extract_text()[:800])

if __name__ == "__main__":
    deep_inspect_nmi()
    deep_inspect_ml_bulletin()
