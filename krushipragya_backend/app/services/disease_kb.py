"""Curated Disease Knowledge Base for KrushiPragya.

Authoritative agricultural disease and pest intelligence sourced from ICAR-CPCRI,
ICAR-DRR (IIRR), ICAR-IISR, and State Agricultural Universities (UAS Bangalore / Dharwad).

STRICT RULE:
This Knowledge Base is 100% deterministic and curated.
NO LLM is used to generate pesticide dosages, chemical treatments, or diagnosis facts.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class DiseaseKnowledgeItem:
    """Curated knowledge entry for a specific crop condition/disease."""
    crop: str
    class_name: str
    disease_name_en: str
    disease_name_kn: str
    scientific_name: Optional[str]
    category: str  # FUNGAL, BACTERIAL, VIRAL, PEST, ABIOTIC, HEALTHY
    symptoms: str
    cultural_control: str
    remedy_en: str
    remedy_kn: str
    source_institution: str


# Mapping: (normalized_crop, normalized_class_name) -> DiseaseKnowledgeItem
_DISEASE_KB: Dict[Tuple[str, str], DiseaseKnowledgeItem] = {
    # ==========================================================================
    # 1. Arecanut (Areca catechu) - 6 classes
    # ==========================================================================
    ("arecanut", "healthy"): DiseaseKnowledgeItem(
        crop="arecanut",
        class_name="Healthy",
        disease_name_en="Healthy Palm / Leaf",
        disease_name_kn="ಆರೋಗ್ಯಕರ ಅಡಿಕೆ ಮರ / ಎಲೆ",
        scientific_name="Areca catechu",
        category="HEALTHY",
        symptoms="Uniform deep green fronds, vigorous crown development, intact spindle, and healthy nut bunches.",
        cultural_control="Ensure adequate field drainage during South-West monsoon. Maintain annual organic mulching and balanced NPK (100:40:140 g/palm).",
        remedy_en="Maintain standard intercultural operations, weed control, and preventive drainage. No chemical treatment required.",
        remedy_kn="ನಿಯಮಿತ ಗೊಬ್ಬರ ಮತ್ತು ನೀರು ನಿರ್ವಹಣೆ ಮುಂದುವರಿಸಿ. ಮಳೆಗಾಲದಲ್ಲಿ ತೋಟದಲ್ಲಿ ನೀರು ನಿಲ್ಲದಂತೆ ಬಸಿದು ಹೋಗಲು ಚರಂಡಿ ಸ್ವಚ್ಛವಾಗಿಡಿ.",
        source_institution="ICAR-CPCRI Kasaragod",
    ),
    ("arecanut", "mahali_koleroga"): DiseaseKnowledgeItem(
        crop="arecanut",
        class_name="Mahali_Koleroga",
        disease_name_en="Koleroga / Mahali (Fruit Rot)",
        disease_name_kn="ಕೊಳೆ ರೋಗ (ಮಹಾಳಿ)",
        scientific_name="Phytophthora meadii",
        category="FUNGAL",
        symptoms="Water-soaked dark green lesions on the surface of tender nuts near calyx, rotting of perianth, heavy shedding of green immature nuts during torrential monsoon.",
        cultural_control="Collect and burn all dropped rotten nuts and dried bunch stalks. Clean the crown prior to monsoon onset.",
        remedy_en="Spray 1% Bordeaux mixture prophylactic spray before the onset of South-West monsoon. Give a second spray 40-45 days later. Alternatively, spray Metalaxyl-Mancozeb @ 2g/L.",
        remedy_kn="ಮುಂಗಾರು ಮಳೆ ಆರಂಭಕ್ಕೂ ಮುನ್ನ ಅಡಿಕೆ ಗೊಂಚಲುಗಳಿಗೆ 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಸಿಂಪಡಿಸಿ. 40-45 ದಿನಗಳ ನಂತರ 2ನೇ ಸಿಂಪಡಣೆ ಮಾಡಿ. ಬಿದ್ದ ಕೊಳೆ ಅಡಿಕೆಗಳನ್ನು ಆರಿಸಿ ನಾಶಪಡಿಸಿ.",
        source_institution="ICAR-CPCRI Kasaragod",
    ),
    ("arecanut", "stem_bleeding"): DiseaseKnowledgeItem(
        crop="arecanut",
        class_name="Stem_bleeding",
        disease_name_en="Stem Bleeding",
        disease_name_kn="ಕಾಂಡ ಒಸರುವ ರೋಗ",
        scientific_name="Thielaviopsis paradoxa",
        category="FUNGAL",
        symptoms="Exudation of dark reddish-brown sticky liquid through stem fissures, localized softening and rotting of internal fibrous trunk tissues.",
        cultural_control="Avoid mechanical injuries to the palm trunk during intercultural operations. Provide adequate summer irrigation.",
        remedy_en="Chisel away infected bark and decayed tissues down to healthy wood. Apply coal tar or Bordeaux paste (10%) to the excised area. Root feed with Hexaconazole @ 2ml in 100ml water.",
        remedy_kn="ಸೋಂಕಿತ ಕಾಂಡದ ಭಾಗವನ್ನು ಕೆತ್ತಿ ತೆಗೆದು ಬೋರ್ಡೋ ಪೇಸ್ಟ್ ಅಥವಾ ಕೋಲ್ಟಾರ್ ಲೇಪಿಸಿ. ಹೆಕ್ಸಾಕೊನಜೋಲ್ 2 ಮಿ.ಲೀ 100 ಮಿ.ಲೀ ನೀರಿಗೆ ಬೆರೆಸಿ ಬೇರಿನ ಮೂಲಕ ನೀಡಿ.",
        source_institution="ICAR-CPCRI Kasaragod",
    ),
    ("arecanut", "bud_borer"): DiseaseKnowledgeItem(
        crop="arecanut",
        class_name="bud borer",
        disease_name_en="Spindle / Bud Borer",
        disease_name_kn="ಸುಳಿ ಕೊರೆಯುವ ಹುಳು",
        scientific_name="Carvalhoia arecae",
        category="PEST",
        symptoms="Bore holes on emerging tender spindle leaf accompanied by chewed fibrous frass; leaflets exhibit ragged edges and shot-holes when unfolding.",
        cultural_control="Regular crown inspection to spot early spindle damage. Clean dry spathes and dead leaf sheaths harboring larvae.",
        remedy_en="Place Phorate 10G or Cartap hydrochloride granules (5g) mixed with equal quantity of sand in the topmost leaf axils, or spray Chlorantraniliprole 18.5 SC @ 0.3ml/L into the crown.",
        remedy_kn="ಎಲೆಯ ಕಂಕುಳಿನಲ್ಲಿ ಮರಳು ಮಿಶ್ರಿತ ಕೀಟನಾಶಕ ಹರಳುಗಳನ್ನು ಹಾಕಿ ಅಥವಾ ಕ್ಲೋರಾಂಟ್ರಾನಿಲಿಪ್ರೋಲ್ 0.3 ಮಿ.ಲೀ/ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಸುಳಿಗೆ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-CPCRI Kasaragod",
    ),
    ("arecanut", "stem_cracking"): DiseaseKnowledgeItem(
        crop="arecanut",
        class_name="stem cracking",
        disease_name_en="Stem Cracking & Sun Scorch",
        disease_name_kn="ಕಾಂಡ ಬಿರುಕು / ಬಿಸಿಲಿನ ಬೇಗೆ",
        scientific_name="Physiological disorder",
        category="ABIOTIC",
        symptoms="Longitudinal cracking and fissures on the south and south-western exposed surfaces of the trunk due to intense solar radiation and moisture fluctuation.",
        cultural_control="Protect exposed palms on southern/western borders by planting shade trees (e.g. banana) or tying areca leaf sheaths around the trunk.",
        remedy_en="Whitewash the exposed southern and western trunk surface with slaked lime (20% solution). Ensure uniform drip irrigation during dry summer months to prevent moisture stress.",
        remedy_kn="ಬೇಸಿಗೆಯಲ್ಲಿ ಅಡಿಕೆ ಕಾಂಡದ ದಕ್ಷಿಣ ಮತ್ತು ಪಶ್ಚಿಮ ಬದಿಗೆ ಸುಣ್ಣದ ತಿಳಿ ನೀರನ್ನು (20%) ಬಳಿಯಿರಿ. ನಿಯಮಿತ ನೀರಾವರಿ ಒದಗಿಸಿ ಕಾಂಡ ಬಿರಿಯುವುದನ್ನು ತಡೆಯಿರಿ.",
        source_institution="ICAR-CPCRI Kasaragod",
    ),
    ("arecanut", "yellow_leaf_disease"): DiseaseKnowledgeItem(
        crop="arecanut",
        class_name="yellow leaf disease",
        disease_name_en="Yellow Leaf Disease (YLD)",
        disease_name_kn="ಹಳದಿ ಎಲೆ ರೋಗ",
        scientific_name="Phytoplasma (vector: Proutista moesta)",
        category="VIRAL",
        symptoms="Characteristic bright chlorosis/yellowing starting from inner whorl leaflet tips, necrosis of leaf margins, blackening of kernel (choor), stunted crown.",
        cultural_control="Eradicate severely diseased, uneconomic palms. Grow YLD-resistant South Kanara selections or hybrid lines. Plant intercrops for microclimate moderation.",
        remedy_en="Apply balanced nutrition with additional Magnesium Sulphate (500g/palm/year) and organic manure. Spray Imidacloprid @ 0.5ml/L to manage planthopper insect vectors.",
        remedy_kn="ರೋಗಗ್ರಸ್ತ ಅತಿಯಾದ ಮರಗಳನ್ನು ತೆಗೆದುಹಾಕಿ. ಪ್ರತಿ ಮರಕ್ಕೆ ವಾರ್ಷಿಕ 500 ಗ್ರಾಂ ಮೆಗ್ನೀಸಿಯಮ್ ಸಲ್ಫೇಟ್ ಮತ್ತು ಸಾವಯವ ಗೊಬ್ಬರ ನೀಡಿ. ಕೀಟ ವಾಹಕಗಳ ನಿಯಂತ್ರಣಕ್ಕೆ ಕೀಟನಾಶಕ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-CPCRI Kasaragod",
    ),

    # ==========================================================================
    # 2. Paddy (Oryza sativa) - 4 classes
    # ==========================================================================
    ("paddy", "blast"): DiseaseKnowledgeItem(
        crop="paddy",
        class_name="Blast",
        disease_name_en="Rice Blast Disease",
        disease_name_kn="ಭತ್ತದ ಬ್ಲಾಸ್ಟ್ (ಬೆಂಕಿ ರೋಗ)",
        scientific_name="Magnaporthe oryzae (Pyricularia oryzae)",
        category="FUNGAL",
        symptoms="Spindle-shaped elliptical lesions with ashy-gray centers and dark reddish-brown margins on leaves; rotting of panicle neck causing chaffy grains.",
        cultural_control="Avoid excessive nitrogenous fertilizer application; split nitrogen into 3-4 doses. Maintain proper field sanitation.",
        remedy_en="Spray Tricyclazole 75 WP @ 0.6g/L or Isoprothiolane 40 EC @ 1.5ml/L at early tillering and heading stages. Repeat spray if weather remains cloudy with high humidity.",
        remedy_kn="ಟ್ರೈಸೈಕ್ಲಜೋಲ್ 75 ಡಬ್ಲ್ಯೂಪಿ @ 0.6 ಗ್ರಾಂ/ಲೀ ನೀರಿಗೆ ಬೆರೆಸಿ ಸಿಂಪಡಿಸಿ. ಯೂರಿಯಾ ಗೊಬ್ಬರವನ್ನು ಮಿತಿಮೀರಿ ಹಾಕಬೇಡಿ.",
        source_institution="ICAR-IIRR (DRR) Hyderabad",
    ),
    ("paddy", "bacterial_leaf_blight"): DiseaseKnowledgeItem(
        crop="paddy",
        class_name="Bacterial_Leaf_Blight",
        disease_name_en="Bacterial Leaf Blight (BLB)",
        disease_name_kn="ದುಂಡಾಣು ಎಲೆ ಕವಚ ರೋಗ (ಬಿ.ಎಲ್.ಬಿ)",
        scientific_name="Xanthomonas oryzae pv. oryzae",
        category="BACTERIAL",
        symptoms="Water-soaked translucent streaks turning into undulating yellowish-white marginal lesions progressing towards leaf sheath; bacterial ooze beads on lesions in morning.",
        cultural_control="Drain standing field water during outbreak. Avoid clipping seedling tips during transplanting.",
        remedy_en="Drain excess standing water. Spray Streptocycline @ 100mg + Copper Oxychloride @ 1.5g per liter of water. Avoid nitrogen top-dressing until disease subsides.",
        remedy_kn="ಗದ್ದೆಯಲ್ಲಿ ನಿಂತ ನೀರನ್ನು ಬಸಿದು ಹೊರಹಾಕಿ. ಸ್ಟ್ರೆಪ್ಟೊಸೈಕ್ಲಿನ್ 100 ಮಿ.ಗ್ರಾಂ + ಕಾಪರ್ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ 1.5 ಗ್ರಾಂ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-IIRR (DRR) Hyderabad",
    ),
    ("paddy", "brown_plant_hopper"): DiseaseKnowledgeItem(
        crop="paddy",
        class_name="Brown_Plant_Hopper",
        disease_name_en="Brown Plant Hopper (BPH)",
        disease_name_kn="ಕಂದು ಜಿಗಿಹುಳು (ಬಿಪಿಹೆಚ್)",
        scientific_name="Nilaparvata lugens",
        category="PEST",
        symptoms="'Hopper burn' circular patches of dried, golden-brown dying plants; nymphs and adults clustered at the base of tillers above water level.",
        cultural_control="Create 'kandi' alley pathways (30cm wide every 2 meters) for aeration and light penetration. Alternate wetting and drying (AWD) irrigation.",
        remedy_en="Spray Pymetrozine 50 WG @ 0.6g/L or Triflumezopyrim 10 SC @ 0.5ml/L directed strictly at the base of the paddy plants. Avoid broad-spectrum pyrethroids which cause resurgence.",
        remedy_kn="ಬೆಳೆಯ ಬುಡಕ್ಕೆ ತಲುಪುವಂತೆ ಪೈಮೆಟ್ರೋಜಿನ್ 0.6 ಗ್ರಾಂ/ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಸಿಂಪಡಿಸಿ. ಗದ್ದೆಯಲ್ಲಿ ಪ್ರತಿ 2 ಮೀಟರ್‌ಗೆ 30 ಸೆಂ.ಮೀ ಕವಲು ದಾರಿ ಬಿಡಿ.",
        source_institution="ICAR-IIRR (DRR) Hyderabad",
    ),
    ("paddy", "sheath_blight"): DiseaseKnowledgeItem(
        crop="paddy",
        class_name="Sheath_Blight",
        disease_name_en="Sheath Blight",
        disease_name_kn="ಕವಚ ಕೊಳೆ ರೋಗ",
        scientific_name="Rhizoctonia solani",
        category="FUNGAL",
        symptoms="Oval or irregular greenish-gray water-soaked spots with dark brown margins developing on leaf sheaths near the waterline and creeping upwards to flag leaf.",
        cultural_control="Destroy weed hosts on bunds; avoid dense planting and excessive nitrogenous fertilization.",
        remedy_en="Spray Hexaconazole 5 SC @ 2ml/L or Validamycin 3 L @ 2ml/L thoroughly targeting the lower leaf sheaths at early disease initiation.",
        remedy_kn="ಹೆಕ್ಸಾಕೊನಜೋಲ್ 5 ಎಸ್.ಸಿ @ 2 ಮಿ.ಲೀ/ಲೀ ಅಥವಾ ವ್ಯಾಲಿಡಾಮೈಸಿನ್ 2 ಮಿ.ಲೀ/ಲೀ ನೀರಿಗೆ ಬೆರೆಸಿ ಗಿಡದ ಬುಡದ ಎಲೆ ಕವಚಗಳಿಗೆ ತಲುಪುವಂತೆ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-IIRR (DRR) Hyderabad",
    ),

    # ==========================================================================
    # 3. Coconut (Cocos nucifera) - 5 classes
    # ==========================================================================
    ("coconut", "bud_root_dropping"): DiseaseKnowledgeItem(
        crop="coconut",
        class_name="Bud Root Dropping",
        disease_name_en="Immature Nut & Button Dropping",
        disease_name_kn="ಎಳನೀರು / ಕಾಯಿ ಉದುರುವಿಕೆ",
        scientific_name="Phytophthora palmivora / Boron deficiency",
        category="FUNGAL",
        symptoms="Premature shedding of young female buttons and developing nuts with necrotic black calyx rings.",
        cultural_control="Ensure regular soil basin irrigation during summer; apply farmyard manure and micronutrients.",
        remedy_en="Soil application of Borax @ 50g per palm per year. Spray 1% Bordeaux mixture on the bunches during pre-monsoon shower intervals.",
        remedy_kn="ಪ್ರತಿ ಮರಕ್ಕೆ ವಾರ್ಷಿಕ 50 ಗ್ರಾಂ ಬೋರಾಕ್ಸ್ ಮಣ್ಣಿಗೆ ಹಾಕಿ. ಮಳೆಗಾಲಕ್ಕೂ ಮುನ್ನ ಕಾಯಿ ಗೊಂಚಲುಗಳಿಗೆ 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-CPCRI Kasaragod",
    ),
    ("coconut", "bud_rot"): DiseaseKnowledgeItem(
        crop="coconut",
        class_name="Bud Rot",
        disease_name_en="Bud Rot Disease",
        disease_name_kn="ಸುಳಿ ಕೊಳೆ ರೋಗ",
        scientific_name="Phytophthora palmivora",
        category="FUNGAL",
        symptoms="Yellowing and withering of the youngest spear leaf; central spindle rots completely with putrid odor and can be easily pulled out.",
        cultural_control="Cut and burn all dead bud tissue. Practice preventive hygiene across the plantation before the monsoon season.",
        remedy_en="Excision of rotting bud tissue and application of 10% Bordeaux paste to the crown. Spray surrounding healthy palms with 1% Bordeaux mixture.",
        remedy_kn="ಕೊಳೆತ ಸುಳಿಯನ್ನು ಸ್ವಚ್ಛಗೊಳಿಸಿ ಬೋರ್ಡೋ ಪೇಸ್ಟ್ ಹಚ್ಚಿ. ಅಕ್ಕಪಕ್ಕದ ಮರಗಳಿಗೆ ಮುನ್ನೆಚ್ಚರಿಕೆಯಾಗಿ 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-CPCRI Kasaragod",
    ),
    ("coconut", "gray_leaf_spot"): DiseaseKnowledgeItem(
        crop="coconut",
        class_name="Gray Leaf Spot",
        disease_name_en="Grey Leaf Spot / Blight",
        disease_name_kn="ಬೂದು ಎಲೆ ಮಚ್ಚೆ ರೋಗ",
        scientific_name="Pestalotiopsis palmarum",
        category="FUNGAL",
        symptoms="Minute yellow spots on leaflets enlarging into oval lesions with ashy-gray necrotic centers and prominent dark brown borders.",
        cultural_control="Prune and burn severely blighted lower fronds. Apply balanced potash nutrition to boost foliar resistance.",
        remedy_en="Spray Propiconazole 25 EC @ 1ml/L or Copper Oxychloride @ 3g/L covering both upper and lower leaflet surfaces.",
        remedy_kn="ಹೆಚ್ಚು ರೋಗಬಾಧಿತ ಕೆಳಮಟ್ಟದ ಗರಿಗಳನ್ನು ಕತ್ತರಿಸಿ ನಾಶಪಡಿಸಿ. ಪ್ರೊಪಿಕೊನಜೋಲ್ 1 ಮಿ.ಲೀ/ಲೀ ನೀರಿಗೆ ಬೆರೆಸಿ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-CPCRI Kasaragod",
    ),
    ("coconut", "leaf_rot"): DiseaseKnowledgeItem(
        crop="coconut",
        class_name="Leaf Rot",
        disease_name_en="Leaf Rot Disease",
        disease_name_kn="ಎಲೆ ಕೊಳೆ ರೋಗ",
        scientific_name="Colletotrichum gloeosporioides",
        category="FUNGAL",
        symptoms="Blackening and rotting of distal leaflet tips in emerging spear leaves; leaves break away leaving a frayed, fan-shaped appearance.",
        cultural_control="Improve drainage in waterlogged soils. Apply adequate potash and magnesium fertilizers.",
        remedy_en="Pour fungicide solution of Hexaconazole @ 2ml in 300ml water or Mancozeb @ 3g in 300ml water into the axil of the youngest spindle leaf twice a year.",
        remedy_kn="ಹೆಕ್ಸಾಕೊನಜೋಲ್ 2 ಮಿ.ಲೀ ಅನ್ನು 300 ಮಿ.ಲೀ ನೀರಿಗೆ ಬೆರೆಸಿ ಸುಳಿ ಎಲೆಯ ಕಂಕುಳಿನಲ್ಲಿ ಸುರಿಯಿರಿ (ವರ್ಷಕ್ಕೆ 2 ಬಾರಿ).",
        source_institution="ICAR-CPCRI Kasaragod",
    ),
    ("coconut", "stem_bleeding"): DiseaseKnowledgeItem(
        crop="coconut",
        class_name="Stem Bleeding",
        disease_name_en="Stem Bleeding Disease",
        disease_name_kn="ತೆಂಗಿನ ಕಾಂಡ ಸೋರುವಿಕೆ",
        scientific_name="Ceratocystis paradoxa",
        category="FUNGAL",
        symptoms="Exudation of dark brown rust-colored liquid through longitudinal stem cracks, internal fibrous decay extending upward in the trunk.",
        cultural_control="Avoid tying cattle or creating wounds on the trunk. Apply neem cake (5kg/palm/year) to the soil basin.",
        remedy_en="Chisel out diseased bark tissue, burn chips, apply coal tar followed by Bordeaux paste (10%). Root feed with Tridemorph @ 5ml in 100ml water.",
        remedy_kn="ರೋಗಗ್ರಸ್ತ ತೊಗಟೆಯನ್ನು ಕೆತ್ತಿ ಕೋಲ್ಟಾರ್ ಅಥವಾ ಬೋರ್ಡೋ ಪೇಸ್ಟ್ ಲೇಪಿಸಿ. ಟ್ರೈಡಿಮಾರ್ಫ್ 5 ಮಿ.ಲೀ ಅನ್ನು 100 ಮಿ.ಲೀ ನೀರಿನಲ್ಲಿ ಬೇರಿನ ಮೂಲಕ ನೀಡಿ.",
        source_institution="ICAR-CPCRI Kasaragod",
    ),

    # ==========================================================================
    # 4. Black Pepper (Piper nigrum) - 3 classes
    # ==========================================================================
    ("black_pepper", "footrot"): DiseaseKnowledgeItem(
        crop="black_pepper",
        class_name="Footrot",
        disease_name_en="Quick Wilt / Foot Rot",
        disease_name_kn="ಕಾಳುಮೆಣಸಿನ ಶೀಘ್ರ ಸೊರಗು ರೋಗ (ಬುಡ ಕೊಳೆ)",
        scientific_name="Phytophthora capsici",
        category="FUNGAL",
        symptoms="Sudden blackening of collar and runner shoots at soil line, rapid foliar wilting and total defoliation of the vine within 7-14 days.",
        cultural_control="Ensure proper drainage channels in plantation. Remove runner shoots touching the wet ground during monsoon.",
        remedy_en="Drench vine basin with Copper Oxychloride (0.2%) @ 5-10 L/vine. Spray 1% Bordeaux mixture on the foliage before monsoon and repeat in August-September.",
        remedy_kn="ಗಿಡದ ಬುಡಕ್ಕೆ ಕಾಪರ್ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ 0.2% ದ್ರಾವಣವನ್ನು (5-10 ಲೀಟರ್) ಸುರಿಯಿರಿ. ಎಲೆಗಳಿಗೆ 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),
    ("black_pepper", "pollu_disease"): DiseaseKnowledgeItem(
        crop="black_pepper",
        class_name="Pollu_Disease",
        disease_name_en="Anthracnose / Pollu Disease",
        disease_name_kn="ಪೊಳ್ಳು ರೋಗ (ಆಂಥ್ರಾಕ್ನೋಸ್)",
        scientific_name="Colletotrichum gloeosporioides",
        category="FUNGAL",
        symptoms="Circular brownish-black spots with chlorotic halo on leaves; necrosis of the spike stalk causing hollow, empty, unmarketable berries.",
        cultural_control="Prune excessive shade tree branches to allow adequate sunlight into the black pepper canopy.",
        remedy_en="Spray 1% Bordeaux mixture or Carbendazim-Mancozeb combination @ 2g/L at the time of spike emergence and again at berry formation stage.",
        remedy_kn="ಗರಿ ಬರುವ ಹಂತದಲ್ಲಿ ಮತ್ತು ಕಾಳು ಕಟ್ಟುವ ಹಂತದಲ್ಲಿ 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಅಥವಾ ಕಾರ್ಬೆಂಡಾಜಿಮ್-ಮ್ಯಾಂಕೋಜೆಬ್ 2 ಗ್ರಾಂ/ಲೀ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),
    ("black_pepper", "slow_decline"): DiseaseKnowledgeItem(
        crop="black_pepper",
        class_name="Slow-Decline",
        disease_name_en="Slow Decline / Nematode Wilt",
        disease_name_kn="ನಿಧಾನ ಸೊರಗು ರೋಗ (ಜಂತುಹುಳು ಬಾಧೆ)",
        scientific_name="Meloidogyne incognita & Radopholus similis",
        category="PEST",
        symptoms="Gradual interveinal yellowing of foliage, poor vine vigor, dieback of feeder branches, swelling and rotting of feeder roots.",
        cultural_control="Plant nematode-free rooted cuttings. Incorporate neem cake @ 1-2 kg/vine annually around the basin.",
        remedy_en="Apply biocontrol agent Pochonia chlamydosporia @ 50g/vine mixed in farmyard manure or Carbofuran 3G @ 30g/vine during May-June and September.",
        remedy_kn="ಪ್ರತಿ ಬಳ್ಳಿಗೆ 50 ಗ್ರಾಂ ಪೊಚೋನಿಯಾ ಜೈವಿಕ ಶಿಲೀಂಧ್ರ ಅಥವಾ 1-2 ಕೆಜಿ ಬೇವಿನ ಹಿಂಡಿ ಮಣ್ಣಿಗೆ ಹಾಕಿ ಜಂತುಹುಳುಗಳನ್ನು ನಿಯಂತ್ರಿಸಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),

    # ==========================================================================
    # 5. Cardamom (Elettaria cardamomum) - 3 classes
    # ==========================================================================
    ("cardamom", "blight1000"): DiseaseKnowledgeItem(
        crop="cardamom",
        class_name="Blight1000",
        disease_name_en="Leaf Blight / Azhukal Disease",
        disease_name_kn="ಏಲಕ್ಕಿ ಅಳುಕಲ್ (ಕೊಳೆ ರೋಗ / ಅಂಗಮಾರಿ)",
        scientific_name="Phytophthora meadii",
        category="FUNGAL",
        symptoms="Water-soaked rotting lesions on leaves and capsules, foul-smelling capsule rot leading to heavy premature drop.",
        cultural_control="Clear decaying mulch from plant basins before monsoon. Ensure shade tree management to avoid excessive humidity.",
        remedy_en="Spray 1% Bordeaux mixture prophylactic spray on foliage and drench soil basin with Copper Oxychloride (0.2%) @ 3-5 L/clump prior to heavy rains.",
        remedy_kn="ಮುಂಗಾರು ಮಳೆ ಮುನ್ನ ಗಿಡಗಳಿಗೆ 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಸಿಂಪಡಿಸಿ ಮತ್ತು ಬುಡಕ್ಕೆ ಕಾಪರ್ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ 0.2% ದ್ರಾವಣ ಸುರಿಯಿರಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),
    ("cardamom", "healthy_1000"): DiseaseKnowledgeItem(
        crop="cardamom",
        class_name="Healthy_1000",
        disease_name_en="Healthy Cardamom Clump",
        disease_name_kn="ಆರೋಗ್ಯಕರ ಏಲಕ್ಕಿ ಗಿಡ",
        scientific_name="Elettaria cardamomum",
        category="HEALTHY",
        symptoms="Vibrant lanceolate green leaves, sturdy pseudostems, healthy panicles with well-filled green capsules.",
        cultural_control="Maintain 50% filtered forest shade, regular organic leaf mulching, and consistent root zone moisture.",
        remedy_en="Continue standard agro-forestry shade regulation, weeding, and balanced organic compost application.",
        remedy_kn="ನಿಯಮಿತ ನೆರಳು ಮತ್ತು ತೇವಾಂಶ ನಿರ್ವಹಣೆ ಮುಂದುವರಿಸಿ. ಸಾವಯವ ಗೊಬ್ಬರ ಮತ್ತು ಎಲೆ ಹೊದಿಕೆ ನೀಡಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),
    ("cardamom", "phylosticta_ls_1000"): DiseaseKnowledgeItem(
        crop="cardamom",
        class_name="Phylosticta_LS_1000",
        disease_name_en="Phyllosticta Leaf Spot (Chenthal)",
        disease_name_kn="ಚೆಂತಾಲ್ ಎಲೆ ಮಚ್ಚೆ ರೋಗ",
        scientific_name="Phyllosticta elettariae",
        category="FUNGAL",
        symptoms="Numerous reddish-brown spots with pale yellow chlorotic rings on leaves; lesions coalesce into large dry scorched patches.",
        cultural_control="Collect and burn heavily infected dead leaves. Avoid excessive overhead shade which promotes fungal spore germination.",
        remedy_en="Spray Mancozeb 75 WP @ 2.5g/L or Carbendazim 50 WP @ 1g/L at 15-20 day intervals starting at first symptom appearance.",
        remedy_kn="ಮ್ಯಾಂಕೋಜೆಬ್ 2.5 ಗ್ರಾಂ/ಲೀಟರ್ ಅಥವಾ ಕಾರ್ಬೆಂಡಾಜಿಮ್ 1 ಗ್ರಾಂ/ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಎಲೆಗಳ ಮೇಲೆ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),

    # ==========================================================================
    # 6. Turmeric (Curcuma longa) - 4 classes
    # ==========================================================================
    ("turmeric", "aphids_disease"): DiseaseKnowledgeItem(
        crop="turmeric",
        class_name="Aphids_Disease",
        disease_name_en="Aphid Infestation & Shoot Borer",
        disease_name_kn="ಅರಿಶಿನ ಗಿಡಹೇನು ಮತ್ತು ಸುಳಿ ಕೊರೆಯುವ ಹುಳು",
        scientific_name="Aphis gossypii / Conogethes punctiferalis",
        category="PEST",
        symptoms="Clusters of small insects sucking sap from emerging shoot tips and leaf axils, causing curled, crinkled foliage and yellowing.",
        cultural_control="Prune and destroy shoot-borer infested dead pseudostems. Avoid excessive nitrogen applications.",
        remedy_en="Spray Dimethoate 30 EC @ 1.7ml/L or Neem oil formulation @ 3ml/L targeting the leaf undersides and whorl axils.",
        remedy_kn="ಡೈಮಿಥೋಯೇಟ್ 1.7 ಮಿ.ಲೀ ಅಥವಾ ಬೇವಿನ ಎಣ್ಣೆ 3 ಮಿ.ಲೀ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಎಲೆಗಳ ಹಿಂಬದಿಗೆ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),
    ("turmeric", "blotch"): DiseaseKnowledgeItem(
        crop="turmeric",
        class_name="Blotch",
        disease_name_en="Leaf Blotch Disease",
        disease_name_kn="ಎಲೆ ಒರಟು ಮಚ್ಚೆ ರೋಗ",
        scientific_name="Taphrina maculans",
        category="FUNGAL",
        symptoms="Small, yellow-orange copper spots appearing in large numbers on upper leaf surfaces, gradually turning brownish-gray.",
        cultural_control="Destroy infected foliar crop residue after harvest. Practice 3-year crop rotation.",
        remedy_en="Spray Mancozeb 75 WP @ 2.5g/L or Copper Oxychloride @ 3g/L as soon as initial foliar spots emerge.",
        remedy_kn="ರೋಗದ ಮೊದಲ ಲಕ್ಷಣ ಕಂಡ ತಕ್ಷಣ ಮ್ಯಾಂಕೋಜೆಬ್ 2.5 ಗ್ರಾಂ/ಲೀ ಅಥವಾ ಕಾಪರ್ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ 3 ಗ್ರಾಂ/ಲೀ ನೀರಿಗೆ ಬೆರೆಸಿ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),
    ("turmeric", "healthy_leaf"): DiseaseKnowledgeItem(
        crop="turmeric",
        class_name="Healthy_Leaf",
        disease_name_en="Healthy Turmeric Plant",
        disease_name_kn="ಆರೋಗ್ಯಕರ ಅರಿಶಿನ ಗಿಡ",
        scientific_name="Curcuma longa",
        category="HEALTHY",
        symptoms="Large, erect, oblong lanceolate green leaves without chlorotic margins or necrotic spotting.",
        cultural_control="Maintain thick green leaf mulching on raised beds; ensure adequate potassium nutrition for rhizome development.",
        remedy_en="Continue intercultural weeding, earthing up, and balanced organic FYM application.",
        remedy_kn="ಸಾಲುಗಳ ಮೇಲೆ ಮಣ್ಣು ಏರಿಸಿ, ಹಸಿರೆಲೆ ಹೊದಿಕೆ ಮುಂದುವರಿಸಿ ಮತ್ತು ನೀರು ಸುಲಭವಾಗಿ ಬಸಿದು ಹೋಗುವಂತೆ ನೋಡಿಕೊಳ್ಳಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),
    ("turmeric", "leaf_spot"): DiseaseKnowledgeItem(
        crop="turmeric",
        class_name="Leaf_Spot",
        disease_name_en="Colletotrichum Leaf Spot",
        disease_name_kn="ಎಲೆ ಕಪ್ಪು ಚುಕ್ಕೆ ರೋಗ",
        scientific_name="Colletotrichum curcumae",
        category="FUNGAL",
        symptoms="Elliptical brown spots with grayish centers and yellow halos on leaves; leaves dry and wither prematurely, reducing rhizome yield.",
        cultural_control="Treat rhizomes before planting with fungicide; collect and destroy fallen diseased leaves.",
        remedy_en="Spray Propiconazole 25 EC @ 1ml/L or Azoxystrobin 23 SC @ 1ml/L at 20-day intervals upon initial symptom onset.",
        remedy_kn="ಪ್ರೊಪಿಕೊನಜೋಲ್ 1 ಮಿ.ಲೀ ಅಥವಾ ಅಜೋಕ್ಸಿಸ್ಟ್ರೋಬಿನ್ 1 ಮಿ.ಲೀ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ 20 ದಿನಗಳ ಅಂತರದಲ್ಲಿ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),

    # ==========================================================================
    # 7. Ginger (Zingiber officinale) - 4 classes
    # ==========================================================================
    ("ginger", "damage_pest"): DiseaseKnowledgeItem(
        crop="ginger",
        class_name="Damage-Pest",
        disease_name_en="Shoot Borer & Rhizome Scale Damage",
        disease_name_kn="ಕಾಂಡ ಕೊರೆಯುವ ಹುಳು ಹಾಗೂ ಗಡ್ಡೆ ಹುರುಪೆ ಹುಳು",
        scientific_name="Conogethes punctiferalis / Aspidiella hartii",
        category="PEST",
        symptoms="Bore holes on pseudostems with frass extrusion, dead heart symptom on central tiller; shriveled scales on rhizomes.",
        cultural_control="Remove and destroy shoot borer infested shoots; dip seed rhizomes in Quinalphos 0.05% before storage.",
        remedy_en="Spray Chlorantraniliprole 18.5 SC @ 0.3ml/L or Malathion 50 EC @ 1.5ml/L at fortnightly intervals starting at shoot emergence.",
        remedy_kn="ಕಾಂಡ ಕೊರೆಯುವ ಹುಳು ಕಂಡಾಗ ಕ್ಲೋರಾಂಟ್ರಾನಿಲಿಪ್ರೋಲ್ 0.3 ಮಿ.ಲೀ ಅಥವಾ ಮಲಾಥಿಯಾನ್ 1.5 ಮಿ.ಲೀ/ಲೀ ಸಿಂಪಡಿಸಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),
    ("ginger", "dehydrated"): DiseaseKnowledgeItem(
        crop="ginger",
        class_name="Dehydrated",
        disease_name_en="Moisture Stress & Heat Scorch",
        disease_name_kn="ತೇವಾಂಶ ಕೊರತೆ / ಒಣಗುವಿಕೆ",
        scientific_name="Physiological moisture deficit",
        category="ABIOTIC",
        symptoms="Inward rolling and curling of leaves, scorched leaf tips and margins, stunted tiller growth due to severe dry root zone.",
        cultural_control="Apply thick green leaf mulch (10 t/ha at planting, 5 t/ha at 45 & 90 DAP). Irrigate beds at 4-6 day intervals.",
        remedy_en="Immediate sprinkler irrigation; apply mulch to conserve bed moisture and prevent sun-baking of shallow rhizomes.",
        remedy_kn="ತಕ್ಷಣ ತುಂತುರು ನೀರಾವರಿ ಒದಗಿಸಿ. ಗಡ್ಡೆಗಳ ಮೇಲ್ಭಾಗ ಒಣಗದಂತೆ ಹಸಿರೆಲೆ ಅಥವಾ ಭತ್ತದ ಹುಲ್ಲಿನ ಹೊದಿಕೆ ಹಾಕಿ ತೇವಾಂಶ ಉಳಿಸಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),
    ("ginger", "healthy"): DiseaseKnowledgeItem(
        crop="ginger",
        class_name="Healthy",
        disease_name_en="Healthy Ginger Plant",
        disease_name_kn="ಆರೋಗ್ಯಕರ ಶುಂಠಿ ಗಿಡ",
        scientific_name="Zingiber officinale",
        category="HEALTHY",
        symptoms="Lush green erect pseudostems, vigorous tillering, healthy aromatic rhizome development.",
        cultural_control="Maintain raised bed drainage to prevent monsoon water stagnation; periodic earthing up.",
        remedy_en="Continue regular mulching, weeding, and balanced NPK (75:50:50 kg/ha) nutrition.",
        remedy_kn="ನಿಯಮಿತ ಕಳೆ ನಿರ್ವಹಣೆ, ಮಣ್ಣು ಏರಿಸುವಿಕೆ ಮತ್ತು ಹಸಿರೆಲೆ ಹೊದಿಕೆ ಮುಂದುವರಿಸಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),
    ("ginger", "leaf_blight"): DiseaseKnowledgeItem(
        crop="ginger",
        class_name="Leaf-blight",
        disease_name_en="Soft Rot / Rhizome Rot / Blight",
        disease_name_kn="ಶುಂಠಿ ಮೃದು ಕೊಳೆ ರೋಗ (ಗಡ್ಡೆ ಕೊಳೆ)",
        scientific_name="Pythium aphanidermatum",
        category="FUNGAL",
        symptoms="Water-soaked collar region, yellowing starting from lower leaves moving upwards, foul-smelling soft decaying rhizomes.",
        cultural_control="Provide raised beds (15cm height) with adequate drainage channels. Treat seed rhizomes with Mancozeb @ 3g/L for 30 minutes before planting.",
        remedy_en="Drench affected and surrounding beds with Metalaxyl-Mancozeb @ 2.5g/L or Copper Oxychloride @ 3g/L. Remove and destroy rotten clumps immediately.",
        remedy_kn="ರೋಗಗ್ರಸ್ತ ಗಿಡದ ಬುಡ ಮತ್ತು ಅಕ್ಕಪಕ್ಕದ ಸಾಲುಗಳಿಗೆ ಮೆಟಾಲಾಕ್ಸಿಲ್-ಮ್ಯಾಂಕೋಜೆಬ್ 2.5 ಗ್ರಾಂ/ಲೀ ಅಥವಾ ಕಾಪರ್ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ 3 ಗ್ರಾಂ/ಲೀ ನೀರಿಗೆ ಬೆರೆಸಿ ಸುರಿಯಿರಿ.",
        source_institution="ICAR-IISR Kozhikode",
    ),
}

# Public alias for external test suites and services
DISEASE_KNOWLEDGE_BASE = _DISEASE_KB


def normalize_class_key(class_name: str) -> str:
    """Normalize class name string for case-insensitive dictionary lookup."""
    return class_name.strip().lower().replace(" ", "_").replace("-", "_")


def get_disease_info(crop: str, class_name: str) -> Optional[DiseaseKnowledgeItem]:
    """Retrieve curated ICAR disease information for a predicted class.
    
    Args:
        crop: Normalized crop identifier (e.g. arecanut, paddy)
        class_name: Model predicted class label (e.g. Mahali_Koleroga, Blast)
        
    Returns:
        DiseaseKnowledgeItem or None if class not found in KB.
    """
    crop_norm = crop.strip().lower().replace("-", "_").replace(" ", "_")
    class_norm = normalize_class_key(class_name)

    # Direct match
    if (crop_norm, class_norm) in _DISEASE_KB:
        return _DISEASE_KB[(crop_norm, class_norm)]

    # Fuzzy prefix/alias match
    for (k_crop, k_class), item in _DISEASE_KB.items():
        if k_crop == crop_norm:
            if k_class in class_norm or class_norm in k_class:
                return item

    return None
