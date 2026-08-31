import pdfplumber
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

fpath = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FACILITIES\IBM\1763377395691b00f36d15cML_PL_2024.pdf"

KNOWN_MINERALS = [
    'Aluminous Laterite', 'Amethyst', 'Apatite', 'Bauxite', 'Beryl', 'Borax', 'Chromite',
    'Copper Ore', 'Copper', 'Diamond', 'Emerald', 'Epidote', 'Fluorite', 'Fluorspar', 'Garnet',
    'Gemstone Cats Eye', 'Gold', 'Graphite', 'Iolite', 'Iron Ore', 'Kyanite', 'Laterite',
    'Lead and Zinc Ore', 'Lead & Zinc Ore', 'Limeshell', 'Limestone', 'Magnesite',
    'Manganese Ore', 'Manganese', 'Marl', 'Moulding Sand', 'Perlite', 'Phosphorite',
    'Rock Phosphate', 'Ruby', 'Selenite', 'Semi Precious Stone', 'Sillimanite', 'Tin',
    'Vermiculite', 'Wollastonite', 'Dunite', 'Pyrophyllite', 'Quartzite', 'Silica Sand'
]

INDIAN_STATES = [
    'Andhra Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat',
    'Haryana', 'Himachal Pradesh', 'Jammu & Kashmir(UT)', 'Jammu & Kashmir',
    'Jharkhand', 'Karnataka', 'Kerala', 'Ladakh', 'Madhya Pradesh',
    'Maharashtra', 'Meghalaya', 'Odisha', 'Rajasthan', 'Tamil Nadu',
    'Telangana', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
]

def test_parse():
    with pdfplumber.open(fpath) as pdf:
        # 1. Parse Table 1
        t1_rows = []
        for line in pdf.pages[11].extract_text().split('\n'):
            m = re.match(r'^([A-Za-z\s&\(\)]+?)\s+(\d+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)$', line.strip())
            if m and 'Percentage' not in line and not line.strip().startswith('Total'):
                t1_rows.append({
                    'state': m.group(1).strip(),
                    'lease_count': int(m.group(2)),
                    'lease_area_ha': float(m.group(4))
                })
        print(f"Table 1: {len(t1_rows)} state rows, Leases: {sum(r['lease_count'] for r in t1_rows):,}, Area: {sum(r['lease_area_ha'] for r in t1_rows):,.2f}")

        # 2. Parse Table 2
        t2_rows = []
        for line in pdf.pages[13].extract_text().split('\n'):
            m = re.match(r'^\d+\s+([A-Za-z\s\(\)]+?)\s+(\d+)\s+([\d\.]+)$', line.strip())
            if m:
                t2_rows.append({
                    'mineral': m.group(1).strip(),
                    'lease_count': int(m.group(2)),
                    'lease_area_ha': float(m.group(3))
                })
        print(f"Table 2: {len(t2_rows)} mineral rows, Leases: {sum(r['lease_count'] for r in t2_rows):,}, Area: {sum(r['lease_area_ha'] for r in t2_rows):,.2f}")

        # 3. Parse Table 3
        current_state = None
        current_district = None
        t3_records = []
        
        for p_idx in range(14, 28):
            raw_text = pdf.pages[p_idx].extract_text() or ''
            lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
            
            i = 0
            while i < len(lines):
                line = lines[i]
                if 'Table- 3' in line or 'Table-3' in line or 'Table 3' in line or '(contd' in line or 'State District' in line or line.isdigit() or '(concld)' in line:
                    i += 1
                    continue
                if line.startswith('Total'):
                    i += 1
                    continue
                
                # Check state
                for st in sorted(INDIAN_STATES, key=len, reverse=True):
                    if line.startswith(st):
                        current_state = st
                        line = line[len(st):].strip()
                        break
                
                # Check if numbers are on next line (multi-line wrapping)
                if not re.search(r'\d+\s+[\d\.]+$', line) and i + 1 < len(lines):
                    next_l = lines[i+1]
                    if re.match(r'^\d+\s+[\d\.]+$', next_l) and i + 2 < len(lines) and not re.search(r'\d', lines[i+2]):
                        # Format: Line1: 'Semi Precious', Line2: '13 125.898', Line3: 'Stone'
                        line = line + ' ' + lines[i+2] + ' ' + next_l
                        i += 2
                    elif re.search(r'\d+\s+[\d\.]+$', next_l):
                        line = line + ' ' + next_l
                        i += 1
                
                m = re.match(r'^(.*?)\s+(\d+)\s+([\d\.]+)$', line)
                if m:
                    text_part = m.group(1).strip()
                    count = int(m.group(2))
                    area = float(m.group(3))
                    
                    matched_mineral = None
                    for min_name in sorted(KNOWN_MINERALS, key=len, reverse=True):
                        if text_part.lower().endswith(min_name.lower()):
                            matched_mineral = min_name
                            prefix = text_part[:-len(min_name)].strip()
                            if prefix:
                                current_district = prefix
                            break
                    
                    if matched_mineral:
                        t3_records.append({
                            'state': current_state,
                            'district': current_district,
                            'mineral': matched_mineral,
                            'lease_count': count,
                            'lease_area_ha': area,
                            'page': p_idx + 1
                        })
                    else:
                        t3_records.append({
                            'state': current_state,
                            'district': current_district,
                            'mineral': text_part,
                            'lease_count': count,
                            'lease_area_ha': area,
                            'page': p_idx + 1
                        })
                i += 1

        print(f"Table 3: {len(t3_records)} district-mineral rows, Leases: {sum(r['lease_count'] for r in t3_records):,}, Area: {sum(r['lease_area_ha'] for r in t3_records):,.2f}")

        # 4. Parse Tables 4 & 5 (Page 30)
        p30_text = pdf.pages[29].extract_text()
        t4_records = []
        t5_records = []
        current_section = None
        for line in p30_text.split('\n'):
            line = line.strip()
            if 'Table - 4' in line or 'High Mineral Potential' in line:
                current_section = 'HIGH'
                continue
            elif 'Table – 5' in line or 'Medium Mineral Potential' in line:
                current_section = 'MEDIUM'
                continue
            elif 'Sources:' in line or 'Total' in line:
                continue
            
            # Format: '1 Andhra Pradesh SPSR NELLORE 52 4 858.48' or 'Andhra Pradesh NANDYAL 140 2 8855.86'
            m = re.match(r'^(?:\d+\s+)?([A-Za-z\s]+?)\s+([A-Za-z\s]+?)\s+(\d+)\s+(\d+)\s+([\d\.]+)$', line)
            if m and current_section == 'HIGH':
                t4_records.append({
                    'state': m.group(1).strip(),
                    'district': m.group(2).strip(),
                    'potential': 'HIGH',
                    'lease_count': int(m.group(3)),
                    'mineral_count': int(m.group(4)),
                    'lease_area_ha': float(m.group(5))
                })
            elif m and current_section == 'MEDIUM':
                t5_records.append({
                    'state': m.group(1).strip(),
                    'district': m.group(2).strip(),
                    'potential': 'MEDIUM',
                    'lease_count': int(m.group(3)),
                    'mineral_count': int(m.group(4)),
                    'lease_area_ha': float(m.group(5))
                })
        print(f"Table 4 (High Potential): {len(t4_records)} districts, Leases: {sum(r['lease_count'] for r in t4_records):,}, Area: {sum(r['lease_area_ha'] for r in t4_records):,.2f}")
        print(f"Table 5 (Medium Potential): {len(t5_records)} districts, Leases: {sum(r['lease_count'] for r in t5_records):,}, Area: {sum(r['lease_area_ha'] for r in t5_records):,.2f}")

        # 5. Parse Table 6 (Page 31)
        p31_text = pdf.pages[30].extract_text()
        t6_records = []
        for line in p31_text.split('\n'):
            line = line.strip()
            # Match state with district count, lease count, and area
            # Format: '1 Andhra Pradesh 12 185 15936.51' (often across 2 lines e.g. '1 Andhra Pradesh' followed by '12 185 15936.51')
            m = re.match(r'^(?:\d+\s+)?([A-Za-z\s&\*\(\)]+?)\s+(\d+)\s+(\d+)\s+([\d\.]+)$', line)
            if m and not line.startswith('Total') and not line.startswith('State'):
                st = m.group(1).replace('*', '').strip()
                t6_records.append({
                    'state': st,
                    'potential': 'LOW',
                    'district_count': int(m.group(2)),
                    'lease_count': int(m.group(3)),
                    'lease_area_ha': float(m.group(4))
                })
        print(f"Table 6 (Low Potential): {len(t6_records)} state summaries, Leases: {sum(r['lease_count'] for r in t6_records):,}, Area: {sum(r['lease_area_ha'] for r in t6_records):,.2f}")

if __name__ == "__main__":
    test_parse()
