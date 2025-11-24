from ics import Calendar

building_code_to_url = {
    "AND": "https://campusmap.ufl.edu/#/index/0007",
    "ARC": "https://campusmap.ufl.edu/#/index/0268",
    "BAR": "https://campusmap.ufl.edu/#/index/0747",
    "BLA": "https://campusmap.ufl.edu/#/index/0724",
    "BRO": "https://campusmap.ufl.edu/#/index/0759",
    "BRY": "https://campusmap.ufl.edu/#/index/0006",
    "BUC": "https://campusmap.ufl.edu/#/index/0015",
    "CAR": "https://campusmap.ufl.edu/#/index/0022",
    "CHE": "https://campusmap.ufl.edu/#/index/0723",
    "CHM": "https://campusmap.ufl.edu/#/index/0028",
    "COM": "https://campusmap.ufl.edu/#/index/0203",
    "CSE": "https://campusmap.ufl.edu/#/index/0042",
    "CON": "https://campusmap.ufl.edu/#/index/0687",
    "CRI": "https://campusmap.ufl.edu/#/index/0031",
    "DAU": "https://campusmap.ufl.edu/#/index/0111",
    "DEN": "https://campusmap.ufl.edu/#/index/0205",
    "DIC": "https://campusmap.ufl.edu/#/index/0181",
    "EMA": "https://campusmap.ufl.edu/#/index/0060",
    "EMB": "https://campusmap.ufl.edu/#/index/0116",
    "EEL": "https://campusmap.ufl.edu/#/index/0668",
    "ELM": "https://campusmap.ufl.edu/#/index/0465",
    "ESB": "https://campusmap.ufl.edu/#/index/0725",
    "FAA": "https://campusmap.ufl.edu/#/index/0597",
    "FAB": "https://campusmap.ufl.edu/#/index/0598",
    "FAC": "https://campusmap.ufl.edu/#/index/0599",
    "FAD": "https://campusmap.ufl.edu/#/index/0269",
    "FLE": "https://campusmap.ufl.edu/#/index/0134",
    "FNT": "https://campusmap.ufl.edu/#/index/0008",
    "FLG": "https://campusmap.ufl.edu/#/index/0021",
    "FSB": "https://campusmap.ufl.edu/#/index/0475",
    "GRA": "https://campusmap.ufl.edu/#/index/0201",
    "GFH": "https://campusmap.ufl.edu/#/index/0010",
    "GRI": "https://campusmap.ufl.edu/#/index/0002",
    "HMA": "https://campusmap.ufl.edu/#/index/0309",
    "HUM": "https://campusmap.ufl.edu/#/index/0579",
    "JEN": "https://campusmap.ufl.edu/#/index/0596",
    "LAR": "https://campusmap.ufl.edu/#/index/0714",
    "LEI": "https://campusmap.ufl.edu/#/index/0009",
    "LIE": "https://campusmap.ufl.edu/#/index/0005",
    "LIW": "https://campusmap.ufl.edu/#/index/0689",
    "LIT": "https://campusmap.ufl.edu/#/index/0655",
    "MSL": "https://campusmap.ufl.edu/#/index/0043",
    "MAT": "https://campusmap.ufl.edu/#/index/0406",
    "MCA": "https://campusmap.ufl.edu/#/index/0495",
    "MCB": "https://campusmap.ufl.edu/#/index/0496",
    "MCC": "https://campusmap.ufl.edu/#/index/0497",
    "MCD": "https://campusmap.ufl.edu/#/index/0498",
    "MEB": "https://campusmap.ufl.edu/#/index/0720",
    "MEL": "https://campusmap.ufl.edu/#/index/0183",
    "MCS": "https://campusmap.ufl.edu/#/index/0226",
    "MUS": "https://campusmap.ufl.edu/#/index/0117",
    "NEW": "https://campusmap.ufl.edu/#/index/0013",
    "NZH": "https://campusmap.ufl.edu/#/index/0832",
    "NOR": "https://campusmap.ufl.edu/#/index/0101",
    "NOA": "https://campusmap.ufl.edu/#/index/0103",
    "OCC": "https://campusmap.ufl.edu/#/index/0094",
    "PEB": "https://campusmap.ufl.edu/#/index/0004",
    "PHY": "https://campusmap.ufl.edu/#/index/0104",
    "PSF": "https://campusmap.ufl.edu/#/index/1200",
    "PHE": "https://campusmap.ufl.edu/#/index/0863",
    "PSY": "https://campusmap.ufl.edu/#/index/0749",
    "PXA": "https://campusmap.ufl.edu/#/index/0294",
    "RAW": "https://campusmap.ufl.edu/#/index/0265",
    "REI": "https://campusmap.ufl.edu/#/index/0686",
    "RHI": "https://campusmap.ufl.edu/#/index/0184",
    "ROG": "https://campusmap.ufl.edu/#/index/0474",
    "ROL": "https://campusmap.ufl.edu/#/index/0012",
    "SMA": "https://campusmap.ufl.edu/#/index/0005",
    "STU": "https://campusmap.ufl.edu/#/index/0029",
    "TIG": "https://campusmap.ufl.edu/#/index/0026",
    "TUR": "https://campusmap.ufl.edu/#/index/0267",
    "VAN": "https://campusmap.ufl.edu/#/index/0023",
    "WAL": "https://campusmap.ufl.edu/#/index/0002",
    "WEI": "https://campusmap.ufl.edu/#/index/0024",
    "WIL": "https://campusmap.ufl.edu/#/index/0100"
}

def process_ics_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    calendar = Calendar(content)
    results = []

    for event in calendar.events:
        location = event.location if event.location else ""
        code = location[:3].upper()
        url = building_code_to_url.get(code, "No URL found for this location code")

        event_info = {
            "event": event.name,
            "location_code": code,
            "location_url": url
        }
        results.append(event_info)

    return results

# Example usage:
# file_path = r"D:\Downloads New\ufschedule\UFSchedule (1).ics"
# events = process_ics_file(file_path)
# for e in events:
#     print(e)
