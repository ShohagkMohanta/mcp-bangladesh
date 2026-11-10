import json
import os
from datetime import datetime, timezone

DIVISIONS_AND_DISTRICTS = {
    "Dhaka": ["Dhaka", "Faridpur", "Gazipur", "Gopalganj", "Kishoreganj", "Madaripur", "Manikganj", "Munshiganj", "Narayanganj", "Narsingdi", "Rajbari", "Shariatpur", "Tangail"],
    "Chattogram": ["Bandarban", "Brahmanbaria", "Chandpur", "Chattogram", "Cumilla", "Cox's Bazar", "Feni", "Khagrachhari", "Lakshmipur", "Noakhali", "Rangamati"],
    "Rajshahi": ["Bogura", "Chapainawabganj", "Joypurhat", "Naogaon", "Natore", "Pabna", "Rajshahi", "Sirajganj"],
    "Khulna": ["Bagerhat", "Chuadanga", "Jashore", "Jhenaidah", "Khulna", "Kushtia", "Magura", "Meherpur", "Narail", "Satkhira"],
    "Barishal": ["Barguna", "Barishal", "Bhola", "Jhalokati", "Patuakhali", "Pirojpur"],
    "Sylhet": ["Habiganj", "Moulvibazar", "Sunamganj", "Sylhet"],
    "Rangpur": ["Dinajpur", "Gaibandha", "Kurigram", "Lalmonirhat", "Nilphamari", "Panchagarh", "Rangpur", "Thakurgaon"],
    "Mymensingh": ["Jamalpur", "Mymensingh", "Netrokona", "Sherpur"]
}

MAJOR_RIVERS = [
    {"name": "Padma", "bn_name": "পদ্মা", "length_km": 366, "transboundary": True, "origin": "Ganges (India)", "outfall": "Meghna at Chandpur", "key_districts": ["Chapainawabganj", "Rajshahi", "Pabna", "Kushtia", "Rajbari", "Faridpur", "Munshiganj", "Shariatpur"]},
    {"name": "Jamuna", "bn_name": "যমুনা", "length_km": 240, "transboundary": True, "origin": "Brahmaputra (Assam)", "outfall": "Padma at Goalundo", "key_districts": ["Kurigram", "Gaibandha", "Bogura", "Jamalpur", "Sirajganj", "Tangail", "Pabna"]},
    {"name": "Meghna (Upper & Lower)", "bn_name": "মেঘনা", "length_km": 264, "transboundary": False, "origin": "Confluence of Surma and Kushiyara", "outfall": "Bay of Bengal", "key_districts": ["Kishoreganj", "Brahmanbaria", "Narsingdi", "Munshiganj", "Chandpur", "Lakshmipur", "Bhola"]},
    {"name": "Teesta", "bn_name": "তিস্তা", "length_km": 115, "transboundary": True, "origin": "Sikkim Himalayas", "outfall": "Jamuna at Chilmari", "key_districts": ["Nilphamari", "Lalmonirhat", "Rangpur", "Kurigram", "Gaibandha"]},
    {"name": "Surma", "bn_name": "সুরমা", "length_km": 249, "transboundary": True, "origin": "Barak River (Manipur/Assam)", "outfall": "Meghna at Kuliarchar", "key_districts": ["Sylhet", "Sunamganj", "Habiganj", "Kishoreganj"]},
    {"name": "Kushiyara", "bn_name": "কুশিয়ারা", "length_km": 161, "transboundary": True, "origin": "Barak River at Amalshid", "outfall": "Meghna at Bhairab", "key_districts": ["Sylhet", "Moulvibazar", "Habiganj"]},
    {"name": "Karatoa", "bn_name": "করতোয়া", "length_km": 257, "transboundary": False, "origin": "Nilphamari / Panchagarh", "outfall": "Bangali River in Bogura", "key_districts": ["Panchagarh", "Dinajpur", "Rangpur", "Gaibandha", "Bogura"]},
    {"name": "Atrai", "bn_name": "আত্রাই", "length_km": 269, "transboundary": True, "origin": "Karatoa in Panchagarh / West Bengal", "outfall": "Hurasagar in Pabna", "key_districts": ["Dinajpur", "Naogaon", "Natore", "Pabna", "Rajshahi"]},
    {"name": "Bangali", "bn_name": "বাঙালি", "length_km": 203, "transboundary": False, "origin": "Nilphamari / Gaibandha", "outfall": "Jamuna / Hurasagar", "key_districts": ["Gaibandha", "Bogura", "Sirajganj"]},
    {"name": "Buriganga", "bn_name": "বুড়িগঙ্গা", "length_km": 29, "transboundary": False, "origin": "Turag / Dhaleshwari near Aminbazar", "outfall": "Dhaleshwari at Narayanganj", "key_districts": ["Dhaka", "Narayanganj"]},
    {"name": "Karnaphuli", "bn_name": "কর্ণফুলী", "length_km": 131, "transboundary": True, "origin": "Lushai Hills (Mizoram)", "outfall": "Bay of Bengal at Patenga", "key_districts": ["Rangamati", "Chattogram"]},
    {"name": "Halda", "bn_name": "হালদা", "length_km": 98, "transboundary": False, "origin": "Badnatali Hills (Khagrachhari)", "outfall": "Karnaphuli at Kalurghat", "key_districts": ["Khagrachhari", "Chattogram"]},
    {"name": "Gorai-Madhumati", "bn_name": "গড়াই-মধুমতি", "length_km": 306, "transboundary": False, "origin": "Padma at Kushtia", "outfall": "Baleshwar Estuary", "key_districts": ["Kushtia", "Jhenaidah", "Magura", "Faridpur", "Narail", "Gopalganj", "Bagerhat"]},
    {"name": "Gumti", "bn_name": "গোমতী", "length_km": 95, "transboundary": True, "origin": "Tripura Hills", "outfall": "Meghna at Daudkandi", "key_districts": ["Cumilla"]},
    {"name": "Muhuri", "bn_name": "মুহুরী", "length_km": 62, "transboundary": True, "origin": "Lushai Hills (Tripura)", "outfall": "Feni River Estuary", "key_districts": ["Feni"]}
]

def main():
    os.makedirs("data", exist_ok=True)
    districts_flat = []
    for div, dists in DIVISIONS_AND_DISTRICTS.items():
        for d in dists:
            districts_flat.append({"district": d, "division": div})
            
    out = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_divisions": len(DIVISIONS_AND_DISTRICTS),
        "total_districts": len(districts_flat),
        "divisions": DIVISIONS_AND_DISTRICTS,
        "districts": districts_flat,
        "major_rivers": MAJOR_RIVERS
    }
    
    with open("data/bd_catalog.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        
    print(f"saved catalog with {len(districts_flat)} districts and {len(MAJOR_RIVERS)} river profiles")

if __name__ == "__main__":
    main()
