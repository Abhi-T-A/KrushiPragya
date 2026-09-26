from app.database.connection import SessionLocal
from app.models.government import GovernmentScheme
from datetime import datetime, timezone
import uuid

db = SessionLocal()
count = db.query(GovernmentScheme).count()
print(f"Current schemes count: {count}")

schemes_data = [
    {
        "id": uuid.UUID("11111111-2222-3333-4444-555555555551"),
        "title": "PM-KISAN Samman Nidhi",
        "title_kn": "PM-Kisan ಸಮೃದ್ಧಿ ಯೋಜನೆ",
        "department": "ಕೃಷಿ ಮತ್ತು ರೈತ ಕಲ್ಯಾಣ ಇಲಾಖೆ",
        "state": "ಭಾರತ",
        "category": "ಆದಾಯ ಬೆಂಬಲ",
        "description": "Annual income support of Rs 6,000 to eligible farmer families across the country.",
        "description_kn": "PM-Kisan ಯೋಜನೆಯ ಪ್ರಯೋಜನ ದೇಶದ ಸಣ್ಣ ಮತ್ತು ಅಂಚು ರೈತ ಕುಟುಂಬಗಳಿಗೆ ವಾರ್ಷಿಕ ಆದಾಯ ಬೆಂಬಲ ಒದಗಿಸುವುದು.",
        "eligibility": "Small and marginal landholding farmer families.",
        "eligibility_kn": "• ಸಣ್ಣ ಮತ್ತು ಅಂಚು ರೈತರು\n• ವೈಯಕ್ತಿಕ/ಕುಟುಂಬ ಕೃಷಿಭೂಮಿ ಹೊಂದಿರುವವರು\n• ಸರ್ಕಾರ ನೀಡಿದ ಇತರ ಕೆಲ ನಿಯಮಗಳು ಅನ್ವಯ",
        "benefits": "Financial assistance of Rs 6,000 per year in 3 equal installments directly into bank account.",
        "benefits_kn": "• ವಾರ್ಷಿಕ ₹6,000 ಹಣಕಾಸು ಸಹಾಯ\n• ₹2,000 ರಂತೆ 3 ಕಂತುಗಳಲ್ಲಿ ನೇರವಾಗಿ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ\n• ರೈತರ ಆರ್ಥಿಕ ಸ್ಥಿರತೆಗಾಗಿ ಸಹಾಯ",
        "application_process": "Apply online via pmkisan.gov.in or CSC center.",
        "application_process_kn": "• ಅಧಿಕೃತ myScheme ಅಥವಾ pmkisan.gov.in ಪೋರ್ಟಲ್‌ಗೆ ಭೇಟಿ ನೀಡಿ\n• ಆಧಾರ್ ಮತ್ತು ಬ್ಯಾಂಕ್ ಖಾತೆ ವಿವರಗಳನ್ನು ನಮೂದಿಸಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ",
        "source_name": "myScheme",
        "source_url": "https://www.myscheme.gov.in/schemes/pm-kisan",
        "application_url": "https://pmkisan.gov.in",
        "last_verified_at": datetime(2024, 9, 12, tzinfo=timezone.utc),
        "status": "ACTIVE",
    },
    {
        "id": uuid.UUID("11111111-2222-3333-4444-555555555552"),
        "title": "Pradhan Mantri Krishi Sinchayee Yojana",
        "title_kn": "ಕೃಷಿ ಸಿಂಚಾಯಿ ಯೋಜನೆ",
        "department": "ಜಲ ಸಂಪನ್ಮೂಲ ಇಲಾಖೆ",
        "state": "ಭಾರತ",
        "category": "ಸಿಂಚಾಯಿ",
        "description": "Per Drop More Crop - micro irrigation and water management subsidies.",
        "description_kn": "ಹನಿ ನೀರಾವರಿ ಮತ್ತು ತುಂತುರು ನೀರಾವರಿ ಪದ್ಧತಿಗಳಿಗೆ ಸಬ್ಸಿಡಿ ಒದಗಿಸಿ ಪ್ರತಿ ಹನಿ ನೀರಿನಲ್ಲಿ ಹೆಚ್ಚು ಬೆಳೆ ಪಡೆಯುವ ಗುರಿ.",
        "eligibility": "Farmers with cultivated land and confirmed water source.",
        "eligibility_kn": "• ಎಲ್ಲಾ ವರ್ಗದ ಕೃಷಿಕರು\n• ಸ್ವಂತ ಜಮೀನು ಮತ್ತು ನೀರಿನ ಮೂಲ ಹೊಂದಿರುವ ರೈತರು\n• ಹನಿ ನೀರಾವರಿ ಅಳವಡಿಸಲು ಇಚ್ಛಿಸುವವರು",
        "benefits": "Subsidy up to 70% to 90% for drip and sprinkler irrigation installations.",
        "benefits_kn": "• ಹನಿ ನೀರಾವರಿ ಅಳವಡಿಕೆಗೆ ಶೇ. 70 ರಿಂದ 90 ರವರೆಗೆ ಸಹಾಯಧನ\n• ನೀರಿನ ಮಿತವ್ಯಯ ಮತ್ತು ಬೆಳೆ ಇಳುವರಿ ಹೆಚ್ಚಳ\n• ವಿದ್ಯುತ್ ಹಾಗೂ ಶ್ರಮದ ಉಳಿತಾಯ",
        "application_process": "Apply at District Horticulture or Agriculture department.",
        "application_process_kn": "• ತಾಲೂಕು ಅಥವಾ ಜಿಲ್ಲಾ ಕೃಷಿ/ತೋಟಗಾರಿಕಾ ಇಲಾಖೆಯನ್ನು ಸಂಪರ್ಕಿಸಿ\n• ಪಹಣಿ ಮತ್ತು ಜಮೀನಿನ ನಕ್ಷೆ ಸಲ್ಲಿಸಿ",
        "source_name": "myScheme",
        "source_url": "https://www.myscheme.gov.in/schemes/pmksy",
        "application_url": "https://pmksy.gov.in",
        "last_verified_at": datetime(2024, 9, 10, tzinfo=timezone.utc),
        "status": "ACTIVE",
    },
    {
        "id": uuid.UUID("11111111-2222-3333-4444-555555555553"),
        "title": "PM-KUSUM",
        "title_kn": "ಕುಸುಮ್ ಯೋಜನೆ",
        "department": "ನವೀಕರಿಸಬಹುದಾದ ಇಂಧನ ಇಲಾಖೆ",
        "state": "ಭಾರತ",
        "category": "ಸೌರ ಶಕ್ತಿ",
        "description": "Subsidized standalone solar-powered agriculture pumps for off-grid irrigation.",
        "description_kn": "ಕೃಷಿ ನೀರಾವರಿ ಪಂಪ್‌ಸೆಟ್‌ಗಳಿಗೆ ಸೌರ ಶಕ್ತಿ ಘಟಕ ಅಳವಡಿಸಲು ಭಾರಿ ಸಬ್ಸಿಡಿ ನೀಡುವ ಯೋಜನೆ.",
        "eligibility": "Individual farmers, water user associations, and cooperatives.",
        "eligibility_kn": "• ವೈಯಕ್ತಿಕ ರೈತರು, ರೈತ ಉತ್ಪಾದಕ ಸಂಸ್ಥೆಗಳು (FPOs)\n• ನೀರಾವರಿ ಸಂಪರ್ಕವಿಲ್ಲದ ಅಥವಾ ಡೀಸೆಲ್ ಪಂಪ್ ಬಳಸುವ ರೈತರಿಗೆ ಆದ್ಯತೆ",
        "benefits": "60% subsidy and 30% bank loan for solar agricultural pumps.",
        "benefits_kn": "• ಸೌರ ಪಂಪ್ ಅಳವಡಿಕೆಗೆ ಶೇ. 60 ಸಬ್ಸಿಡಿ ಮತ್ತು ಶೇ. 30 ಬ್ಯಾಂಕ್ ಸಾಲ\n• ಉಚಿತ ಸೌರ ವಿದ್ಯುತ್ ಹಾಗೂ ಹೆಚ್ಚುವರಿ ವಿದ್ಯುತ್ ಮಾರಾಟದ ಅವಕಾಶ\n• 25 ವರ್ಷಗಳ ಕಾಲ ನಿರಂತರ ವಿದ್ಯುತ್",
        "application_process": "Online application through state nodal renewable energy agency.",
        "application_process_kn": "• ರಾಜ್ಯ ನವೀಕರಿಸಬಹುದಾದ ಇಂಧನ ಅಭಿವೃದ್ಧಿ ನಿಯಮಿತ (KREDL) ಪೋರ್ಟಲ್ ಮೂಲಕ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ",
        "source_name": "myScheme",
        "source_url": "https://www.myscheme.gov.in/schemes/pm-kusum",
        "application_url": "https://pmkusum.mnre.gov.in",
        "last_verified_at": datetime(2024, 9, 5, tzinfo=timezone.utc),
        "status": "ACTIVE",
    },
    {
        "id": uuid.UUID("11111111-2222-3333-4444-555555555554"),
        "title": "Pradhan Mantri Fasal Bima Yojana",
        "title_kn": "ರೈತ ವಿಮಾ ಯೋಜನೆ",
        "department": "ಕೃಷಿ ಮತ್ತು ರೈತ ಕಲ್ಯಾಣ ಇಲಾಖೆ",
        "state": "ಭಾರತ",
        "category": "ವಿಮೆ",
        "description": "Comprehensive crop insurance against natural calamities, pests and diseases.",
        "description_kn": "ಪ್ರಕೃತಿ ವಿಕೋಪ, ಅಕಾಲಿಕ ಮಳೆ, ಬರ ಮತ್ತು ರೋಗಗಳಿಂದ ಬೆಳೆ ನಷ್ಟವಾದರೆ ರೈತರಿಗೆ ಪೂರ್ಣ ಆರ್ಥಿಕ ಪರಿಹಾರ ಒದಗಿಸುವ ಯೋಜನೆ.",
        "eligibility": "All farmers growing notified crops in notified areas including sharecroppers and tenant farmers.",
        "eligibility_kn": "• ಅಧಿಸೂಚಿತ ಬೆಳೆ ಬೆಳೆಯುವ ಎಲ್ಲಾ ರೈತರು\n• ಗೇಣಿದಾರರು ಹಾಗೂ ಸ್ವಂತ ಜಮೀನುದಾರರು",
        "benefits": "Minimal premium (Kharif 2%, Rabi 1.5%) with full sum insured coverage for yield loss.",
        "benefits_kn": "• ಕನಿಷ್ಠ ಪ್ರೀಮಿಯಂ: ಖಾರಿಫ್ ಶೇ. 2, ರಬಿ ಶೇ. 1.5 ಮಾತ್ರ\n• ಬೆಳೆ ನಾಶವಾದಾಗ ಶೀಘ್ರ ವಿಮಾ ಕ್ಲೈಮ್ ಇತ್ಯರ್ಥ\n• ಬಿತ್ತನೆಯಿಂದ ಕಟಾವಿನ ನಂತರದ ನಷ್ಟಕ್ಕೂ ಪರಿಹಾರ",
        "application_process": "Apply through bank, CSC, or pmfby.gov.in before seasonal cut-off date.",
        "application_process_kn": "• ಸಮೀಪದ ಬ್ಯಾಂಕ್ ಶಾಖೆ, ಸಿಎಸ್‌ಸಿ ಕೇಂದ್ರ ಅಥವಾ pmfby.gov.in ಮೂಲಕ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ",
        "source_name": "myScheme",
        "source_url": "https://www.myscheme.gov.in/schemes/pmfby",
        "application_url": "https://pmfby.gov.in",
        "last_verified_at": datetime(2024, 9, 14, tzinfo=timezone.utc),
        "status": "ACTIVE",
    },
    {
        "id": uuid.UUID("11111111-2222-3333-4444-555555555555"),
        "title": "Raitha Siri Scheme",
        "title_kn": "ರೈತ ಸಿರಿ ಯೋಜನೆ",
        "department": "ಕರ್ನಾಟಕ ಕೃಷಿ ಇಲಾಖೆ",
        "state": "Karnataka",
        "category": "ಸಬ್ಸಿಡಿ",
        "description": "Financial assistance for millet growers in Karnataka.",
        "description_kn": "ಸಿರಿಧಾನ್ಯ ಬೆಳೆಯುವ ಕರ್ನಾಟಕದ ರೈತರಿಗೆ ಹೆಕ್ಟೇರ್‌ಗೆ ₹10,000 ನೇರ ಆರ್ಥಿಕ ಪ್ರೋತ್ಸಾಹಧನ.",
        "eligibility": "Millet cultivators in Karnataka with land records.",
        "eligibility_kn": "• ಕರ್ನಾಟಕದ ಸಿರಿಧಾನ್ಯ ಬೆಳೆಯುವ ರೈತರು\n• ಗರಿಷ್ಠ 2 ಹೆಕ್ಟೇರ್ ವರೆಗೆ ಸೌಲಭ್ಯ",
        "benefits": "Direct benefit transfer of Rs 10,000 per hectare for millet farming.",
        "benefits_kn": "• ಹೆಕ್ಟೇರ್‌ಗೆ ₹10,000 ನೇರ ನಗದು ವರ್ಗಾವಣೆ (DBT)\n• ಸಿರಿಧಾನ್ಯ ಬೀಜ ಹಾಗೂ ಯಂತ್ರೋಪಕರಣಗಳಿಗೆ ವಿಶೇಷ ಸಬ್ಸಿಡಿ",
        "application_process": "Register through Raitha Samparka Kendra or FRUITS portal.",
        "application_process_kn": "• ರೈತ ಸಂಪರ್ಕ ಕೇಂದ್ರ ಅಥವಾ FRUITS ಪೋರ್ಟಲ್ ಮೂಲಕ ನೋಂದಾಯಿಸಿ",
        "source_name": "Raitha Mitra",
        "source_url": "https://raitamitra.karnataka.gov.in",
        "application_url": "https://raitamitra.karnataka.gov.in",
        "last_verified_at": datetime(2024, 9, 8, tzinfo=timezone.utc),
        "status": "ACTIVE",
    },
]

for s in schemes_data:
    existing = db.query(GovernmentScheme).filter(GovernmentScheme.id == s["id"]).first()
    if not existing:
        scheme_obj = GovernmentScheme(**s)
        db.add(scheme_obj)
        print(f"Added {s['title']}")
    else:
        for k, v in s.items():
            setattr(existing, k, v)
        print(f"Updated {s['title']}")

db.commit()
db.close()
print("Seeding completed successfully!")
