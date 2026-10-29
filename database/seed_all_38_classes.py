"""
seed_all_38_classes.py
Seeds comprehensive agricultural knowledge for all 38 PlantVillage classes
into the PostgreSQL database without dropping or altering existing tables.
"""

import sys
import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Load database URL from root .env
ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

# -------------------------------------------------------------------------
# DATA DEFINITIONS FOR ALL 38 CLASSES
# -------------------------------------------------------------------------

CROPS_DATA = [
    ("Apple", "Malus domestica", "Temperate tree fruit widely grown for fresh consumption, prone to fungal scabs, rots, and rusts."),
    ("Blueberry", "Vaccinium corymbosum", "Perennial flowering shrub producing tart-sweet berries, thriving in acidic, well-drained soils."),
    ("Cherry", "Prunus cerasus", "Stone fruit cultivated in temperate regions, susceptible to powdery mildew and leaf spot pathogens."),
    ("Corn", "Zea mays", "Major cereal grain and staple food crop vulnerable to foliar fungal leaf blights, rusts, and leaf spots."),
    ("Grape", "Vitis vinifera", "Vigorous woody vine fruit grown for fruit, juice, and wine; susceptible to black rot, esca, and mildew."),
    ("Orange", "Citrus sinensis", "Evergreen citrus tree producing sweet oranges, severely threatened by vector-borne citrus greening."),
    ("Peach", "Prunus persica", "Deciduous fruit tree producing juicy stone fruits, vulnerable to bacterial spots and leaf curl."),
    ("Pepper, Bell", "Capsicum annuum", "Warm-season solanaceous vegetable cultivated for crisp sweet peppers; vulnerable to bacterial spot."),
    ("Raspberry", "Rubus idaeus", "Bramble fruit shrub with cane-growth habit, requiring cool-temperate climate and good soil drainage."),
    ("Soybean", "Glycine max", "High-protein legume crop cultivated globally for oil and meal; monitored for foliar blights and rusts."),
    ("Squash", "Cucurbita pepo", "Vigorous cucurbit vegetable crop with broad leaves, commonly affected by foliar powdery mildews."),
    ("Strawberry", "Fragaria × ananassa", "Low-growing perennial berry crop prone to foliar leaf scorch, leaf spot, and gray mold.")
]

# 38 Classes metadata
# format: (prediction_key, crop_name, disease_name, description, symptoms_list, causes_list, treatments_data, prevention_list)
# treatments_data format: list of (treatment_name, type, description, instructions, precautions, rate_data)
# rate_data format: (method, unit, rate, basis, notes) or None

KNOWLEDGE_BASE = [
    # 0: Apple Scab
    (
        "Apple___Apple_scab", "Apple", "Apple Scab",
        "A major fungal disease caused by Venturia inaequalis that attacks leaves, blossoms, and fruits, leading to olive-green to black velvety scabs.",
        [
            ("Olive-green to black velvety lesions on leaves", "Spots start on leaf undersides and turn dark brown or olive-black with velvety fungal spores."),
            ("Distorted and puckered leaves", "Severe infections cause leaves to twist, cup, dry out, and drop prematurely."),
            ("Cork-like scabby fruit spots", "Infected fruit develops dark scabby patches that crack and stunt fruit development.")
        ],
        [
            ("Fungus Venturia inaequalis", "Overwinters in fallen apple leaf debris and releases ascospores during spring rains."),
            ("Prolonged leaf wetness", "Requires 6-12 hours of continuous surface leaf wetness at 15-24°C for spore germination."),
            ("Dense canopy shade", "Poor interior airflow maintains high humidity and leaf dampness.")
        ],
        [
            ("Fungicidal scab management", "Chemical control",
             "Protective and curative foliar fungicides to prevent spore penetration during active infection periods.",
             "Apply protective fungicides beginning at green tip stage and repeat at 7-10 day intervals through petal fall.",
             "Follow label re-entry intervals and rotate modes of action to prevent fungal resistance.",
             ("Foliar spray", "g/acre", 600.0, "per acre", "Mancozeb 75% WP or Captan 50% WP. Citing TNAU Agritech / State Horticultural extension. Follow product label."))
        ],
        [
            ("Sanitize fallen leaves", "Mow or remove fallen apple leaves in autumn to reduce primary overwintering inocula."),
            ("Prune for airflow", "Prune tree canopy annually in late winter to facilitate rapid leaf drying."),
            ("Select resistant cultivars", "Plant scab-resistant cultivars such as Liberty, Prima, or Enterprise where available.")
        ]
    ),

    # 1: Apple Black Rot
    (
        "Apple___Black_rot", "Apple", "Apple Black Rot",
        "A destructive fungal disease caused by Botryosphaeria obtusa causing frogeye leaf spots, limb cankers, and firm black rot of fruits.",
        [
            ("Frogeye leaf spots", "Small purple specks enlarge to circular spots with tan centers and defined dark margins."),
            ("Decaying black fruit rot", "Fruit develops expanding brown to black concentric rings, turning into a firm mummified rot."),
            ("Branch and twig cankers", "Bark darkens and sinks, creating cracked elliptical cankers on branches.")
        ],
        [
            ("Botryosphaeria obtusa fungus", "Survives in dead wood, branch cankers, and mummified fruits left in the tree canopy."),
            ("Warm rainy weather", "Optimal infection occurs between 20-27°C accompanied by rain showers.")
        ],
        [
            ("Protective fungicide spray", "Chemical control",
             "Foliar fungicide applications to protect young leaves and expanding fruitlets from spore infection.",
             "Spray from pink-bud through petal-fall at 10-14 day intervals.",
             "Do not spray near open water bodies; wear protective PPE.",
             ("Foliar spray", "g/acre", 500.0, "per acre", "Captan 50% WP or Thiophanate-methyl 70% WP. Source: Agricultural Extension Service. Verify local product registration."))
        ],
        [
            ("Remove mummified fruit", "Collect and destroy all dried, mummified fruits hanging on branches or on the ground."),
            ("Prune out cankers", "Prune out dead wood, cankered branches, and fire blight strikes during dormant season.")
        ]
    ),

    # 2: Apple Cedar Rust
    (
        "Apple___Cedar_apple_rust", "Apple", "Cedar Apple Rust",
        "A heteroecious fungal rust caused by Gymnosporangium juniperi-virginianae that alternates between eastern red cedar/juniper and apple trees.",
        [
            ("Bright orange-yellow leaf spots", "Small pale yellow spots on upper leaf surfaces expand into bright orange lesions with red borders."),
            ("Fruiting fungal aecia on undersides", "Underside of spots develops raised tube-like projection rings that release rust spores."),
            ("Premature defoliation", "Heavy leaf infections lead to widespread early leaf fall.")
        ],
        [
            ("Gymnosporangium rust fungus", "Requires both apple and nearby cedar/juniper species to complete its complex two-year life cycle."),
            ("Spring rainfall events", "Spore-producing gelatinous galls on junipers swell in rain and discharge spores that blow onto apples.")
        ],
        [
            ("Rust-targeted foliar treatment", "Chemical control",
             "Foliar sterol-inhibitor or multi-site protective sprays during spring leaf emergence.",
             "Apply from tight cluster through petal fall when juniper galls are active.",
             "Rotate fungicide classes to preserve efficacy.",
             ("Foliar spray", "ml/acre", 150.0, "per acre", "Myclobutanil 10% WP or Difenoconazole 25% EC. Source: State Hort. Extension Guidelines."))
        ],
        [
            ("Remove nearby junipers", "Remove eastern red cedar trees within a 1-2 mile radius of the orchard where practical."),
            ("Choose resistant apple varieties", "Plant resistant varieties such as Redfree, Freedom, or Enterprise.")
        ]
    ),

    # 3: Apple Healthy
    (
        "Apple___healthy", "Apple", "Apple Healthy",
        "Healthy apple foliage with normal green coloration, intact leaf margins, and vigorous photosynthetic performance without signs of active pathology.",
        [
            ("Uniform green foliage", "Smooth, vibrant green leaves free of chlorosis, necrosis, or spotting."),
            ("Intact leaf margins", "No curling, puckering, or ragged lesions along leaf borders."),
            ("Normal growth vigor", "Firm turgor with normal terminal shoot development and healthy fruit spurs.")
        ],
        [
            ("Optimal orchard maintenance", "Balanced nutrient supply, adequate soil moisture, proper pruning, and sanitary orchard management.")
        ],
        [
            ("Standard orchard maintenance", "Cultural management",
             "Routine cultural maintenance without therapeutic agrochemical inputs.",
             "Maintain balanced drip or localized irrigation, organic mulching, and periodic canopy observation.",
             "No chemical pesticide application is indicated for healthy foliage.",
             None)
        ],
        [
            ("Routine canopy inspection", "Scout leaves weekly during spring and early summer for early pest or disease appearance."),
            ("Sanitary orchard care", "Remove fallen twigs and maintain clean weed-free tree strips.")
        ]
    ),

    # 4: Blueberry Healthy
    (
        "Blueberry___healthy", "Blueberry", "Blueberry Healthy",
        "Healthy blueberry foliage demonstrating vigorous vegetative growth, glossy green leaves, and absence of fungal or viral symptoms.",
        [
            ("Glossy dark green leaves", "Smooth elliptical leaves with vibrant green coloration and uniform texture."),
            ("Normal vegetative shoots", "Strong terminal shoot growth with no dieback or cankering.")
        ],
        [
            ("Optimal acidic soil conditions", "Maintained soil pH of 4.5-5.5 with adequate moisture and good organic drainage.")
        ],
        [
            ("Routine bush maintenance", "Cultural management",
             "Maintain optimal soil acidity, organic pine bark mulching, and uniform micro-irrigation.",
             "Apply sulfur amendments if pH drifts upward; no disease control chemicals required.",
             "Always test soil before fertilizer additions.",
             None)
        ],
        [
            ("Soil pH monitoring", "Check soil pH and moisture twice annually to maintain healthy root zone conditions."),
            ("Drip irrigation management", "Avoid overhead irrigation to minimize foliar moisture.")
        ]
    ),

    # 5: Cherry Powdery Mildew
    (
        "Cherry_(including_sour)___Powdery_mildew", "Cherry", "Cherry Powdery Mildew",
        "A common fungal disease caused by Podosphaera clandestina, causing white powdery fungal patches on new leaves and fruit stems.",
        [
            ("White powdery fungal patches", "Circular patches of talcum-like white fungal mycelium spread across leaf surfaces."),
            ("Leaf distortion and upward curling", "Young infected leaves cup, wrinkle, and become brittle."),
            ("Stunted shoot development", "Terminal shoot tips become covered in white fungal felt and stunt.")
        ],
        [
            ("Podosphaera clandestina fungus", "Overwinters as chasmothecia in bark crevices and fallen leaves, releasing spores in warm weather."),
            ("High humidity with dry foliage", "Unlike many fungi, powdery mildew thrives in high relative humidity without requiring free liquid water.")
        ],
        [
            ("Powdery mildew foliar spray", "Chemical control",
             "Protective and eradicant sulfur or DMI/strobilurin foliar treatments.",
             "Apply at petal fall and repeat at shuck fall or 10-14 days later.",
             "Do not apply sulfur when temperatures exceed 30°C to prevent phytotoxicity.",
             ("Foliar spray", "g/acre", 800.0, "per acre", "Wettable sulfur 80% WDG or Tebuconazole 25.9% EC. Source: TNAU/State Fruit Extension. Follow product label."))
        ],
        [
            ("Prune infected terminal shoots", "Prune and destroy infected shoots during dormant pruning."),
            ("Promote canopy ventilation", "Maintain open tree centers to reduce localized humidity.")
        ]
    ),

    # 6: Cherry Healthy
    (
        "Cherry_(including_sour)___healthy", "Cherry", "Cherry Healthy",
        "Healthy cherry foliage displaying uniform leaf shape, deep green color, intact margins, and robust branch growth.",
        [
            ("Lush green leaves", "Uniform green color with typical serrated leaf margins and firm texture."),
            ("Absence of leaf spots or mildew", "Clean leaf surfaces free of white powder, shot-holes, or yellowing.")
        ],
        [
            ("Balanced tree nutrition and sunlight", "Proper soil fertility, adequate sunlight penetration, and proper drainage.")
        ],
        [
            ("Standard tree care", "Cultural management",
             "Regular orchard care including balanced watering, mulch, and periodic branch thinning.",
             "No disease treatment required for healthy trees.",
             "Continue monitoring foliage regularly.",
             None)
        ],
        [
            ("Periodic foliar scouting", "Inspect trees every 7-10 days throughout the active growing season."),
            ("Proper winter pruning", "Prune trees in late winter to maintain vigor and open structure.")
        ]
    ),

    # 7: Corn Gray Leaf Spot
    (
        "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot", "Corn", "Corn Gray Leaf Spot",
        "A serious foliar fungal disease of maize caused by Cercospora zeae-maydis, forming characteristic rectangular gray to tan lesions.",
        [
            ("Narrow rectangular lesions", "Tan to gray lesions bounded by leaf veins, forming distinct rectangular spots 1-5 cm long."),
            ("Blighting and premature leaf death", "Lesions coalesce, blighting entire leaves and reducing grain fill."),
            ("Loss of green leaf area", "Upper leaves dry out prematurely, leading to stalk lodging and reduced yield.")
        ],
        [
            ("Cercospora zeae-maydis fungus", "Survives in corn crop residue on the soil surface."),
            ("Warm, humid, foggy weather", "Extended periods of high relative humidity (>90%) and warm temperatures (25-32°C).")
        ],
        [
            ("Foliar fungicide application", "Chemical control",
             "Apply targeted foliar fungicides at VT (tasseling) to R1 (silking) stage if disease progresses.",
             "Spray when disease reaches the third leaf below the ear prior to or at tasseling.",
             "Observe harvest interval guidelines.",
             ("Foliar spray", "ml/acre", 200.0, "per acre", "Azoxystrobin 18.2% + Difenoconazole 11.4% SC. Source: ICAR/Corn Pathology Guidelines. Follow product label."))
        ],
        [
            ("Crop rotation", "Rotate corn with non-host crops like soybeans to break the disease cycle."),
            ("Residue management", "Incorporate or manage infected crop debris to accelerate decomposition."),
            ("Select tolerant hybrids", "Plant maize hybrids with high tolerance to gray leaf spot.")
        ]
    ),

    # 8: Corn Common Rust
    (
        "Corn_(maize)___Common_rust_", "Corn", "Corn Common Rust",
        "A fungal disease caused by Puccinia sorghi, causing circular to elongate golden-brown to cinnamon-red pustules on both leaf surfaces.",
        [
            ("Cinnamon-brown powdery pustules", "Small, raised, reddish-brown pustules erupt through both upper and lower leaf surfaces."),
            ("Spore release when rubbed", "Pustules rupture the leaf epidermis, releasing powdery rust-colored urediniospores."),
            ("Chlorotic haloes and leaf drying", "Yellow haloes surround heavily clustered pustules, causing leaves to desiccate.")
        ],
        [
            ("Puccinia sorghi fungus", "Blown northward by prevailing spring winds from southern overwintering regions."),
            ("Cool and moist conditions", "Favored by temperatures between 16-24°C with high humidity and morning dew.")
        ],
        [
            ("Rust fungicide treatment", "Chemical control",
             "Apply foliar fungicide if rust pustules appear on upper leaves before silking on susceptible hybrids.",
             "Spray promptly when threshold is reached; ensure good spray coverage.",
             "Follow regional threshold guidelines before spraying.",
             ("Foliar spray", "g/acre", 250.0, "per acre", "Propiconazole 25% EC or Tebuconazole 25.9% EC. Source: Agricultural Extension Guidance. Follow product label."))
        ],
        [
            ("Plant resistant hybrids", "Utilize commercial hybrids bred with Rp resistance genes."),
            ("Timely planting", "Plant early to allow crop maturity before major rust spore flights occur.")
        ]
    ),

    # 9: Corn Northern Leaf Blight
    (
        "Corn_(maize)___Northern_Leaf_Blight", "Corn", "Corn Northern Leaf Blight",
        "A widespread fungal blight caused by Exserohilum turcicum, producing large cigar-shaped, grayish-green to tan lesions.",
        [
            ("Large cigar-shaped lesions", "Elongated elliptical lesions 2.5 to 15 cm long with rounded ends on leaf blades."),
            ("Gray-green turning to tan", "Lesions initially appear water-soaked and gray-green, later drying into tan dead tissue."),
            ("Severe blighting of lower to upper canopy", "Infection starts on lower leaves and rapidly moves upward in wet seasons.")
        ],
        [
            ("Exserohilum turcicum fungus", "Overwinters as mycelium and conidia on infected corn leaf residue."),
            ("Moderate temperatures and frequent rain", "Favored by temperatures between 18-27°C with extended dew or rain showers.")
        ],
        [
            ("Foliar blight control", "Chemical control",
             "Apply protective and systemic fungicides between V12 and R1 growth stages when threshold is exceeded.",
             "Ensure adequate water volume for deep canopy penetration.",
             "Follow label precautions regarding aerial or ground spray drift.",
             ("Foliar spray", "ml/acre", 200.0, "per acre", "Pyraclostrobin + Fluxapyroxad or Azoxystrobin SC. Source: Extension Crop Protection. Follow product label."))
        ],
        [
            ("Tolerant hybrids", "Choose corn hybrids containing Ht resistance genes."),
            ("Tillage and rotation", "Rotate fields out of corn for at least one year in high-tillage systems.")
        ]
    ),

    # 10: Corn Healthy
    (
        "Corn_(maize)___healthy", "Corn", "Corn Healthy",
        "Robust corn foliage showing deep green leaf blades, strong central midribs, uniform growth, and clean vegetative development.",
        [
            ("Vibrant deep green foliage", "Broad, healthy leaves with vibrant green color and absence of lesions or pustules."),
            ("Intact leaf margins and midrib", "No tearing, spotting, stripes, or blighting along leaf edges."),
            ("Strong vegetative vigor", "Proper internode elongation and healthy whorl emergence.")
        ],
        [
            ("Optimal agronomic conditions", "Balanced nitrogen and potassium nutrition, adequate rainfall, and weed-free stands.")
        ],
        [
            ("Standard crop management", "Cultural management",
             "Continue standard agronomic practices including balanced side-dress fertilization and field scouting.",
             "No disease treatment required for healthy corn.",
             "Follow standard pest and weed management schedules.",
             None)
        ],
        [
            ("Routine scouting", "Walk fields at V6, V12, and tasseling stages to verify clean canopy health.")
        ]
    ),

    # 11: Grape Black Rot
    (
        "Grape___Black_rot", "Grape", "Grape Black Rot",
        "A destructive fungal disease of grapes caused by Guignardia bidwellii, attacking all green vine tissues and shriveling berries into hard black mummies.",
        [
            ("Reddish-brown circular leaf spots", "Small brown spots on leaves develop dark borders with tiny black specks (pycnidia) inside."),
            ("Shriveled black mummified berries", "Infected grapes turn pale, rot rapidly, and shrivel into hard, wrinkled black mummies."),
            ("Black elliptical shoot lesions", "Sunken dark purple-black lesions develop on young shoots and petioles.")
        ],
        [
            ("Guignardia bidwellii fungus", "Overwinters in mummified berries on vines or the ground, discharging spores in spring."),
            ("Warm, humid, rainy weather", "Requires 6-24 hours of leaf wetness at 20-27°C for infection.")
        ],
        [
            ("Fungicidal black rot spray", "Chemical control",
             "Protective foliar fungicide program from early shoot growth through 4 weeks post-bloom.",
             "Critical sprays are immediate pre-bloom, bloom, and post-bloom.",
             "Rotate FRAC groups to prevent resistance.",
             ("Foliar spray", "g/acre", 500.0, "per acre", "Mancozeb 75% WP or Azoxystrobin 23% SC. Source: TNAU/Viticulture Extension. Follow product label."))
        ],
        [
            ("Remove mummified clusters", "Remove all mummified fruit clusters during winter pruning and cultivate the vineyard floor."),
            ("Canopy management", "Shoot position and leaf pull to improve sunlight penetration and air movement around clusters.")
        ]
    ),

    # 12: Grape Esca (Black Measles)
    (
        "Grape___Esca_(Black_Measles)", "Grape", "Grape Esca (Black Measles)",
        "A complex trunk disease caused by wood-decay fungi, causing tiger-stripe interveinal leaf necrosis and dark speckled spots on fruit.",
        [
            ("Tiger-stripe leaf pattern", "Interveinal yellow or red stripes develop between leaf veins, followed by dry necrotic margins."),
            ("Measles fruit spotting", "Small dark purple to black speckles appear scattered over berry skins."),
            ("Apoplexy or vine collapse", "Sudden wilting and drying of entire shoots or vines during hot summer days.")
        ],
        [
            ("Fungal trunk pathogens", "Phaeomoniella chlamydospora, Phaeoacremonium minimum, and Fomitiporia species invading pruning wounds."),
            ("Vascular disruption", "Fungal toxins and vessel clogging prevent water transport during peak transpirational demand.")
        ],
        [
            ("Trunk disease sanitation", "Cultural management",
             "Remedial surgery by cutting back infected cordons/trunks below necrotic wood to healthy green tissue.",
             "Paint pruning wounds immediately with approved wound sealant or biocontrol paste.",
             "No curative systemic chemical treatment exists once trunk is colonized.",
             None)
        ],
        [
            ("Delayed pruning", "Prune vines late in the dormant season when wound healing is rapid."),
            ("Wound protection", "Protect large pruning wounds with pruning sealants or Trichoderma-based bio-protectants.")
        ]
    ),

    # 13: Grape Leaf Blight
    (
        "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", "Grape", "Grape Leaf Blight",
        "A foliar fungal disease caused by Pseudocercospora cladosporioides (Isariopsis clavispora), causing large irregular brown leaf spots and early leaf fall.",
        [
            ("Irregular brown necrotic spots", "Dark brown, angular to irregular lesions appear on older leaves, often with faint yellow borders."),
            ("Velvety sporulation on undersides", "Olive-brown velvety fungal tufts form on the underside of spots in humid air."),
            ("Premature defoliation", "Severe infection causes extensive leaf drying, premature defoliation, and reduced sugar accumulation.")
        ],
        [
            ("Pseudocercospora fungus", "Survives in fallen infected leaves and shoots, splashing onto lower canopy leaves during rains."),
            ("High humidity and rainfall", "Frequent rain and persistent dew favor rapid spore germination.")
        ],
        [
            ("Leaf blight foliar spray", "Chemical control",
             "Apply protective copper or broad-spectrum fungicides upon first sign of leaf spotting.",
             "Ensure thorough coverage of lower and interior canopy leaves.",
             "Follow copper application limits to prevent soil accumulation.",
             ("Foliar spray", "g/acre", 600.0, "per acre", "Copper oxychloride 50% WP or Mancozeb 75% WP. Source: TNAU Agritech Grape Portal. Follow product label."))
        ],
        [
            ("Post-harvest vineyard sanitation", "Clean fallen foliage and destroy infected pruning debris after harvest."),
            ("Open canopy architecture", "Trellis and trim vines to promote rapid leaf drying after rain.")
        ]
    ),

    # 14: Grape Healthy
    (
        "Grape___healthy", "Grape", "Grape Healthy",
        "Healthy grapevine foliage displaying characteristic palmately lobed green leaves, vigorous shoot elongation, and clean grape clusters.",
        [
            ("Vibrant green lobed leaves", "Smooth green foliage free of spots, necrosis, curling, or mildew growth."),
            ("Active shoot growth", "Strong tendrils and healthy shoot tips with uniform green coloration.")
        ],
        [
            ("Balanced vineyard management", "Proper soil moisture, appropriate vine nutrition, balanced cropload, and regular canopy management.")
        ],
        [
            ("Standard vineyard care", "Cultural management",
             "Continue standard canopy maintenance, balanced shoot positioning, and regulated irrigation.",
             "No disease treatment required for healthy vines.",
             "Monitor vines regularly for seasonal pests.",
             None)
        ],
        [
            ("Regular canopy scouting", "Scout the vineyard weekly, especially after rain events, to confirm continued health.")
        ]
    ),

    # 15: Orange Citrus Greening
    (
        "Orange___Haunglongbing_(Citrus_greening)", "Orange", "Citrus Greening (Huanglongbing)",
        "A devastating bacterial disease caused by Candidatus Liberibacter asiaticus, transmitted by the Asian citrus psyllid, leading to tree decline.",
        [
            ("Asymmetrical blotchy mottle", "Irregular mottled yellowing across leaf blades that does not mirror the midrib (unlike nutrient deficiency)."),
            ("Yellow shoots on tree sectors", "Individual branches show pronounced yellowing while the rest of the tree appears green."),
            ("Lopsided, bitter fruit with aborted seeds", "Small, misshapen, sour fruit that remains green at the stylar end ('greening').")
        ],
        [
            ("Candidatus Liberibacter bacterium", "Phloem-limited unculturable bacterium that clogs nutrient transport in citrus trees."),
            ("Asian citrus psyllid vector", "Diaphorina citri insect spreads the bacterium from tree to tree during sap feeding.")
        ],
        [
            ("Vector management and tree nutrition", "Integrated management",
             "Control citrus psyllid populations using targeted insecticides and apply intensive foliar micro-nutrient supplements.",
             "Monitor psyllid flushes on young citrus shoots and spray when nymphs or adults are detected.",
             "Infected commercial trees with severe decline should be removed to protect the grove.",
             ("Foliar spray", "ml/acre", 100.0, "per acre", "Imidacloprid 17.8% SL or Thiamethoxam 25% WG for psyllid control. Source: Citrus Research & Education / TNAU. Follow product label."))
        ],
        [
            ("Plant certified disease-free nursery stock", "Use only certified clean trees grown in insect-proof screenhouses."),
            ("Field inspection and rogueing", "Promptly remove and destroy confirmed infected trees to eliminate vector reservoirs.")
        ]
    ),

    # 16: Peach Bacterial Spot
    (
        "Peach___Bacterial_spot", "Peach", "Peach Bacterial Spot",
        "A bacterial disease caused by Xanthomonas campestris pv. pruni affecting leaves, twigs, and fruit of peach trees, causing shot-holes and fruit pitting.",
        [
            ("Angular water-soaked leaf spots", "Small angular purple to dark brown spots form along veins, later dropping out to give a shot-hole effect."),
            ("Pitted, gumming fruit lesions", "Fruit develops circular sunken spots that crack and exude sticky gum."),
            ("Premature leaf yellowing and drop", "Heavily spotted leaves turn yellow and drop prematurely, weakening the tree.")
        ],
        [
            ("Xanthomonas arboricola pv. pruni bacterium", "Overwinters in twig cankers and terminal buds, spreading by blowing rain and dew."),
            ("Warm, windy, wet spring weather", "Optimal development at 21-29°C with frequent rain and wind-blown sand that creates micro-wounds.")
        ],
        [
            ("Bactericidal copper treatment", "Chemical control",
             "Apply preventative copper sprays starting at bud swell through petal fall at low rates to avoid copper phytotoxicity.",
             "Oxytetracycline sprays can be used where approved during post-bloom periods.",
             "Never apply high rates of copper on tender peach foliage.",
             ("Foliar spray", "g/acre", 400.0, "per acre", "Copper hydroxide or Copper oxychloride at low labeled rates. Source: State Fruit Pathology Guidelines. Follow product label."))
        ],
        [
            ("Select tolerant cultivars", "Plant peach cultivars bred for resistance to bacterial spot (e.g. Redhaven, Candor)."),
            ("Maintain tree vigor", "Avoid excessive nitrogen which produces succulent, highly susceptible shoot growth.")
        ]
    ),

    # 17: Peach Healthy
    (
        "Peach___healthy", "Peach", "Peach Healthy",
        "Healthy peach foliage characterized by smooth lanceolate leaves, vibrant green color, clean bark, and vigorous shoot expansion.",
        [
            ("Vibrant lanceolate green leaves", "Smooth, elongated leaves free of shot-holes, bacterial spots, or curling."),
            ("Clean bark and shoot growth", "Smooth twigs without gumming, cankers, or tip dieback.")
        ],
        [
            ("Optimal orchard culture", "Proper sun exposure, adequate irrigation, balanced fertility, and annual dormant pruning.")
        ],
        [
            ("Standard peach maintenance", "Cultural management",
             "Maintain clean tree basins, weed control, and balanced seasonal irrigation.",
             "No disease treatment required for healthy trees.",
             "Scout foliage periodically for early pest activity.",
             None)
        ],
        [
            ("Routine orchard scouting", "Inspect peach foliage weekly throughout spring and early summer.")
        ]
    ),

    # 18: Pepper Bell Bacterial Spot
    (
        "Pepper,_bell___Bacterial_spot", "Pepper, Bell", "Pepper Bacterial Spot",
        "A destructive disease of bell pepper caused by Xanthomonas campestris pv. vesicatoria, producing small dark water-soaked spots on leaves and fruit.",
        [
            ("Water-soaked angular leaf spots", "Small circular to angular water-soaked spots turn dark brown with pale yellow borders."),
            ("Raised blister-like spots on fruit", "Immature green peppers develop raised rough, scab-like, or blistered brown spots."),
            ("Heavy leaf drop and sunscald", "Severe foliar infection causes defoliation, exposing peppers to direct sunscald damage.")
        ],
        [
            ("Xanthomonas campestris pv. vesicatoria bacterium", "Seed-borne pathogen surviving in crop debris, spreading via splashing rain and overhead irrigation."),
            ("High temperature and humidity", "Favored by temperatures of 24-30°C and extended periods of leaf wetness.")
        ],
        [
            ("Bactericide foliar spray", "Chemical control",
             "Apply copper-based bactericides combined with mancozeb for synergistic bacterial suppression.",
             "Apply preventative sprays on a 7-10 day schedule during humid rainy conditions.",
             "Avoid working in pepper fields when foliage is wet.",
             ("Foliar spray", "g/acre", 600.0, "per acre", "Copper oxychloride 50% WP (600g) + Mancozeb 75% WP (400g). Source: TNAU Agritech / Vegetable Extension. Follow product label."))
        ],
        [
            ("Certified disease-free seed", "Use certified pathogen-free seeds or hot-water treated seeds."),
            ("Crop rotation", "Rotate pepper fields out of solanaceous crops for at least two years."),
            ("Avoid overhead watering", "Utilize drip irrigation to keep leaf surfaces dry.")
        ]
    ),

    # 19: Pepper Bell Healthy
    (
        "Pepper,_bell___healthy", "Pepper, Bell", "Pepper Bell Healthy",
        "Healthy bell pepper plant exhibiting deep green glossy leaves, sturdy erect stems, clean flower buds, and absence of bacterial or viral lesions.",
        [
            ("Glossy dark green leaves", "Smooth, broad, ovate leaves free of spotting, yellowing, or edge curling."),
            ("Sturdy stems and vigorous branching", "Strong vegetative architecture with healthy branching and flower development.")
        ],
        [
            ("Optimal vegetable care", "Warm growing temperatures, well-drained fertile loam, and balanced drip fertigation.")
        ],
        [
            ("Standard vegetable care", "Cultural management",
             "Maintain consistent moisture via drip irrigation, mulch soil, and provide balanced nutrition.",
             "No disease treatment required for healthy plants.",
             "Continue routine monitoring.",
             None)
        ],
        [
            ("Weekly scouting", "Scout pepper foliage and fruit sets weekly for early pest or disease appearance.")
        ]
    ),

    # 20: Potato Early Blight (Already in DB id 5, updated with prediction_key)
    # 21: Potato Late Blight (Already in DB id 4, updated with prediction_key)

    # 22: Potato Healthy
    (
        "Potato___healthy", "Potato", "Potato Healthy",
        "Healthy potato foliage with rich green compound leaves, vigorous canopy spread, clean stems, and no signs of fungal blight or mosaic.",
        [
            ("Rich green compound leaves", "Uniform green color across all leaflets, free of concentric rings, water-soaking, or wilt."),
            ("Full vegetative canopy", "Erect, strong stems supporting vigorous tuber bulking beneath the soil.")
        ],
        [
            ("Good agronomic management", "Certified seed tubers, fertile soil with proper hilling, and regulated irrigation.")
        ],
        [
            ("Standard crop care", "Cultural management",
             "Maintain proper ridge hilling, consistent soil moisture, and balanced potassium nutrition.",
             "No disease treatment required for healthy potato crops.",
             "Follow regular crop monitoring routines.",
             None)
        ],
        [
            ("Routine field inspection", "Inspect field twice weekly, especially when weather turns cool and damp.")
        ]
    ),

    # 23: Raspberry Healthy
    (
        "Raspberry___healthy", "Raspberry", "Raspberry Healthy",
        "Healthy raspberry foliage showing vibrant green serrated leaves on strong canes with clean stems and vigorous growth.",
        [
            ("Vibrant serrated leaves", "Healthy composite leaves with bright green tops and silvery undersides, free of spots."),
            ("Clean cane growth", "Erect primocanes without lesions, spur blights, or anthracnose cankers.")
        ],
        [
            ("Proper bramble management", "Good air circulation, trellising, well-drained organic soil, and annual pruning.")
        ],
        [
            ("Standard cane management", "Cultural management",
             "Maintain trellising, remove spent floricanes after fruiting, and ensure good base airflow.",
             "No disease treatment required for healthy raspberry plants.",
             "Monitor for cane borers and mites.",
             None)
        ],
        [
            ("Cane thinning and airflow", "Thin canes to maintain 4-6 inches between stems for optimal sunlight and air.")
        ]
    ),

    # 24: Soybean Healthy
    (
        "Soybean___healthy", "Soybean", "Soybean Healthy",
        "Healthy soybean foliage with trifoliate deep green leaves, sturdy stem nodules, and clean vegetative canopy without rust or frogeye spots.",
        [
            ("Trifoliate deep green leaves", "Smooth, healthy trifoliate leaves with vibrant coloration and no foliar necrosis."),
            ("Robust vegetative canopy", "Uniform field canopy with vigorous flowering and pod development.")
        ],
        [
            ("Optimal legume agronomy", "Good soil inoculation, balanced phosphorus-potassium fertility, and good weed control.")
        ],
        [
            ("Standard agronomic care", "Cultural management",
             "Maintain weed-free canopy and inspect leaves for late-season pests.",
             "No disease treatment required for healthy soybean stands.",
             "Continue standard management schedule.",
             None)
        ],
        [
            ("Canopy scouting", "Scout fields at vegetative stage and reproductive pod-fill stage.")
        ]
    ),

    # 25: Squash Powdery Mildew
    (
        "Squash___Powdery_mildew", "Squash", "Squash Powdery Mildew",
        "A common fungal disease caused by Podosphaera xanthii, producing dense white powdery fungal growth on cucurbit leaves and stems.",
        [
            ("White powdery fungal talc", "Circular white powdery spots appear on upper and lower leaf surfaces, quickly coalescing to cover leaves."),
            ("Premature leaf senescence", "Infected leaves turn yellow, brown, and dry up crisp, exposing squash fruit to sunscald."),
            ("Reduced fruit yield and sweetness", "Loss of photosynthetic area stunts fruit development and lowers sugar content.")
        ],
        [
            ("Podosphaera xanthii fungus", "Airborne conidia travel long distances, germinating even on dry leaves under humid conditions."),
            ("Dense planting and shade", "Favored by warm temperatures (20-28°C), high relative humidity, and filtered sunlight.")
        ],
        [
            ("Powdery mildew foliar spray", "Chemical control",
             "Apply protective and systemic fungicides or bio-fungicides at the earliest sign of white powdery spots.",
             "Spray both upper and lower leaf surfaces thoroughly.",
             "Rotate fungicide chemical classes to prevent resistance development.",
             ("Foliar spray", "g/acre", 400.0, "per acre", "Wettable sulfur 80% WDG or Azoxystrobin 23% SC. Source: TNAU Vegetable Protection Portal. Follow product label."))
        ],
        [
            ("Plant resistant squash varieties", "Select powdery mildew-resistant squash hybrids where available."),
            ("Proper plant spacing", "Allow adequate space between hills or rows to maximize airflow and sunlight.")
        ]
    ),

    # 26: Strawberry Leaf Scorch
    (
        "Strawberry___Leaf_scorch", "Strawberry", "Strawberry Leaf Scorch",
        "A fungal disease caused by Diplocarpon earlianum, forming numerous small, dark purple irregular blotches that scorch foliage.",
        [
            ("Dark purple angular blotches", "Small purplish spots on upper leaf surfaces lack the white center typical of leaf spot."),
            ("Scorched, burned leaf appearance", "Blotches coalesce until entire leaf blades turn brown, dry, and look scorched by fire."),
            ("Curled leaf margins", "Infected leaf edges curl upward and wither prematurely.")
        ],
        [
            ("Diplocarpon earlianum fungus", "Overwinters in infected strawberry leaves and crowns; spores splash spread during rains."),
            ("Persistent leaf wetness and warm weather", "Prolonged leaf wetness and temperatures between 20-25°C.")
        ],
        [
            ("Foliar fungicide spray", "Chemical control",
             "Apply preventative fungicides early in spring as new growth begins, repeating through bloom.",
             "Direct spray thoroughly into the crown and under leaf surfaces.",
             "Follow pre-harvest interval (PHI) strictly before picking berries.",
             ("Foliar spray", "g/acre", 500.0, "per acre", "Captan 50% WP or Thiophanate-methyl 70% WP. Source: Strawberry Extension Guide. Follow product label."))
        ],
        [
            ("Renovate strawberry beds", "Mow and remove old leaves immediately after harvest renovation."),
            ("Use drip irrigation", "Avoid overhead sprinklers to prevent splashing fungal spores.")
        ]
    ),

    # 27: Strawberry Healthy
    (
        "Strawberry___healthy", "Strawberry", "Strawberry Healthy",
        "Healthy strawberry plant showing trifoliate, glossy green leaves, intact serrated edges, vigorous crown development, and clean blossoms.",
        [
            ("Glossy trifoliate green leaves", "Vibrant green leaves free of purple blotches, leaf spots, or scorched edges."),
            ("Robust crown and runners", "Vigorous crown growth producing clean white flowers and healthy fruit trusses.")
        ],
        [
            ("Optimal strawberry culture", "Well-drained raised beds, plastic or straw mulch, balanced drip fertigation, and adequate sunlight.")
        ],
        [
            ("Standard berry maintenance", "Cultural management",
             "Maintain clean straw or plastic mulch under fruit, ensure uniform drip moisture, and weed promptly.",
             "No disease treatment required for healthy strawberry plants.",
             "Continue routine scouting.",
             None)
        ],
        [
            ("Bed sanitation", "Remove senescing leaves and runner offshoots to keep crowns open and ventilated.")
        ]
    ),

    # 28: Tomato Bacterial Spot
    (
        "Tomato___Bacterial_spot", "Tomato", "Tomato Bacterial Spot",
        "A destructive disease caused by Xanthomonas campestris pv. vesicatoria, producing small dark water-soaked spots with yellow haloes.",
        [
            ("Small dark water-soaked spots", "Small brown-black angular spots on leaves, often surrounded by a prominent yellow halo."),
            ("Scabby, raised black spots on green fruit", "Fruit shows raised black rough scabs that crack open, reducing marketability."),
            ("Extensive leaf yellowing and blighting", "Heavy infection leads to yellowing, defoliation, and sunscald of exposed fruit.")
        ],
        [
            ("Xanthomonas bacteria", "Seed-borne pathogen surviving in crop residue, spreading rapidly via rain splash and overhead irrigation."),
            ("Warm, humid, rainy weather", "Favored by temperatures between 24-30°C and frequent rain showers.")
        ],
        [
            ("Bactericide spray program", "Chemical control",
             "Apply preventative copper bactericide tank-mixed with mancozeb for improved bacterial efficacy.",
             "Begin sprays at transplanting and repeat every 7-10 days during rainy conditions.",
             "Avoid cultivating or handling tomato plants when leaves are wet.",
             ("Foliar spray", "g/acre", 600.0, "per acre", "Copper oxychloride 50% WP (600g) + Mancozeb 75% WP (400g). Source: TNAU Agritech Tomato Portal. Follow product label."))
        ],
        [
            ("Use certified pathogen-free seed", "Plant certified clean seeds and inspected disease-free nursery transplants."),
            ("Rotate crops", "Rotate away from tomatoes, peppers, and eggplants for at least 2-3 years."),
            ("Drip irrigation only", "Keep foliage dry by avoiding sprinkler or overhead irrigation.")
        ]
    ),

    # 29: Tomato Early Blight (Already in DB id 2, updated with prediction_key)
    # 30: Tomato Late Blight (Already in DB id 1, updated with prediction_key)
    # 31: Tomato Leaf Mold (Already in DB id 3, updated with prediction_key)

    # 32: Tomato Septoria Leaf Spot
    (
        "Tomato___Septoria_leaf_spot", "Tomato", "Tomato Septoria Leaf Spot",
        "A common fungal disease caused by Septoria lycopersici, producing numerous small circular spots with gray centers and dark margins.",
        [
            ("Small circular spots with gray centers", "Circular lesions 1-3 mm wide with light gray to tan centers and defined dark brown borders."),
            ("Tiny black specks in spot center", "Microscopic fungal pycnidia appear as black dots inside the gray centers of spots."),
            ("Progressive upward defoliation", "Starts on lowest leaves and progresses upward rapidly, leading to complete leaf drop.")
        ],
        [
            ("Septoria lycopersici fungus", "Overwinters in tomato crop residue, solanaceous weeds (nightshade), and on stakes."),
            ("Warm, wet, and humid conditions", "Requires wet leaf surfaces and temperatures between 20-25°C for rapid infection.")
        ],
        [
            ("Foliar fungicide spray", "Chemical control",
             "Apply protective fungicides starting when lowest leaves show initial spots and repeat every 7-10 days.",
             "Ensure thorough coverage of lower and dense interior foliage.",
             "Follow label harvest interval instructions strictly.",
             ("Foliar spray", "g/acre", 600.0, "per acre", "Chlorothalonil 75% WP or Mancozeb 75% WP. Source: TNAU / University Extension. Follow product label."))
        ],
        [
            ("Mulch base of plants", "Apply organic or plastic mulch around plant bases to prevent soil splash onto lower leaves."),
            ("Stake and prune lower leaves", "Stake plants and remove the bottom 12 inches of foliage to improve ventilation."),
            ("Rotate away from solanaceous crops", "Practice a 3-year rotation away from tomatoes, potatoes, and peppers.")
        ]
    ),

    # 33: Tomato Spider Mites
    (
        "Tomato___Spider_mites Two-spotted_spider_mite", "Tomato", "Tomato Spider Mites",
        "Pest infestation by Tetranychus urticae (two-spotted spider mite), causing fine yellow stippling, leaf bronzing, and fine silky webbing.",
        [
            ("Fine yellow stippling on leaves", "Tiny yellow or white specks on upper leaf surfaces where mites suck cell sap."),
            ("Silky webbing on leaf undersides", "Fine silken webbing covers leaf undersides, growing tips, and flower clusters."),
            ("Bronzing, drying, and leaf drop", "Severe infestation causes leaves to turn bronze, dry up completely, and drop.")
        ],
        [
            ("Two-spotted spider mite (Tetranychus urticae)", "Tiny arachnids that multiply extremely rapidly in hot, dry, dusty weather."),
            ("Hot, dry environmental conditions", "High temperatures (>30°C) and low relative humidity trigger population explosions.")
        ],
        [
            ("Acaricide / miticide foliar application", "Pest management",
             "Apply targeted miticide or horticultural insecticidal soap, targeting the undersides of leaves thoroughly.",
             "Repeat application in 5-7 days to control newly hatched nymphs.",
             "Do not spray during full bloom to protect beneficial pollinators.",
             ("Foliar spray", "ml/acre", 200.0, "per acre", "Spiromesifen 22.9% SC or Abamectin 1.9% EC. Source: TNAU Agritech Pest Management. Follow product label."))
        ],
        [
            ("Maintain adequate crop moisture", "Avoid drought stress and wash dusty field borders to discourage mite buildup."),
            ("Encourage predatory mites", "Conserve natural enemies (phytoseiid predatory mites and lady beetles) by avoiding broad-spectrum pyrethroids.")
        ]
    ),

    # 34: Tomato Target Spot
    (
        "Tomato___Target_Spot", "Tomato", "Tomato Target Spot",
        "A fungal disease caused by Corynespora cassiicola, causing circular brown lesions with concentric rings and yellow haloes on leaves and fruit.",
        [
            ("Concentric target-like brown spots", "Brown circular lesions with concentric rings resembling a target board on leaves and stems."),
            ("Sunken target spots on green fruit", "Fruit lesions start small and expand into large, dark, sunken spots with concentric rings."),
            ("Premature defoliation", "Upper canopy leaves turn chlorotic, dry out, and drop prematurely.")
        ],
        [
            ("Corynespora cassiicola fungus", "Survives in crop residue and alternative weed hosts, spreading via wind and rain splash."),
            ("Warm temperatures and high humidity", "Favored by temperatures between 20-30°C with prolonged humidity or frequent rains.")
        ],
        [
            ("Foliar target spot spray", "Chemical control",
             "Apply targeted protective fungicides when symptoms first appear, repeating at 7-14 day intervals.",
             "Maintain continuous spray coverage during prolonged wet weather.",
             "Rotate FRAC groups to prevent resistance.",
             ("Foliar spray", "ml/acre", 200.0, "per acre", "Azoxystrobin 23% SC or Boscalid + Pyraclostrobin. Source: TNAU / State Extension. Follow product label."))
        ],
        [
            ("Improve canopy airflow", "Prune suckers and stake tomato plants to enhance air circulation and rapid drying."),
            ("Sanitize field debris", "Destroy infected crop debris immediately after harvest.")
        ]
    ),

    # 35: Tomato Yellow Leaf Curl Virus
    (
        "Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato", "Tomato Yellow Leaf Curl Virus",
        "A devastating begomovirus transmitted by the sweetpotato whitefly (Bemisia tabaci), causing severe stunting, upward leaf curling, and flower drop.",
        [
            ("Upward leaf cupping and yellowing", "Young leaves curl upwards into cups with pale yellow (chlorotic) margins and reduced size."),
            ("Severe plant stunting", "Internodes shorten drastically, giving plants a compact, bushy, erect appearance."),
            ("Blossom drop and no fruit set", "Flowers drop before pollination, resulting in drastic yield loss if infected early.")
        ],
        [
            ("Tomato yellow leaf curl virus (TYLCV)", "Begomovirus transmitted exclusively by the whitefly Bemisia tabaci during sap feeding."),
            ("High whitefly vector populations", "Warm dry weather promotes rapid reproduction and migration of whitefly vectors.")
        ],
        [
            ("Vector management and infected rogueing", "Integrated virus management",
             "Manage whitefly populations with systemic insecticides and reflective mulches; rogue out infected plants.",
             "Spray whitefly-targeted insecticides during early crop stages when vector pressure is detected.",
             "No chemical cures the plant once infected with the virus; rogue out infected plants early.",
             ("Foliar spray", "g/acre", 80.0, "per acre", "Diafenthiuron 50% WP or Spiromesifen for whitefly vector suppression. Source: TNAU Agritech TYLCV Management. Follow product label."))
        ],
        [
            ("Use TYLCV-resistant hybrids", "Plant resistant tomato hybrids (e.g. varieties with Ty-1, Ty-3 resistance genes)."),
            ("Yellow sticky traps", "Install yellow sticky traps (15-20 per acre) to monitor and reduce whitefly populations."),
            ("Nursery net protection", "Raise seedlings under 40-mesh insect-proof netting to prevent early virus transmission.")
        ]
    ),

    # 36: Tomato Mosaic Virus
    (
        "Tomato___Tomato_mosaic_virus", "Tomato", "Tomato Mosaic Virus",
        "A highly stable tobamovirus causing light and dark green mosaic mottling, distorted strap-like leaves, and uneven fruit ripening.",
        [
            ("Mottled light and dark green leaves", "Leaves show irregular patches of light and dark green mosaic patterns."),
            ("Leaf distortion and shoestringing", "Leaves may become puckered, blistered, or narrow and thread-like ('shoestring' effect)."),
            ("Internal brown fruit browning", "Fruit may display internal browning and uneven, blotchy ripening.")
        ],
        [
            ("Tomato mosaic virus (ToMV)", "Extremely persistent virus transmitted mechanically through hands, tools, grafting, and seeds."),
            ("Mechanical contact", "Transmitted by workers handling plants, pruning tools, and tobacco products.")
        ],
        [
            ("Strict sanitary management", "Sanitary cultural control",
             "Rogue out and destroy infected plants immediately; wash hands and tools thoroughly with soap and water or skim milk.",
             "Workers should wash hands with soap or 20% non-fat dry milk solution before handling seedlings.",
             "No chemical viricides exist; avoid spreading sap to healthy neighboring plants.",
             None)
        ],
        [
            ("Plant resistant varieties", "Use tomato cultivars with Tm-2 or Tm-2^2 resistance genes."),
            ("Disinfect tools", "Disinfect pruning shears and staking materials with 10% trisodium phosphate (TSP) or 10% bleach solution."),
            ("Tobacco ban in greenhouse", "Prohibit smoking or tobacco handling around tomato crops.")
        ]
    ),

    # 37: Tomato Healthy
    (
        "Tomato___healthy", "Tomato", "Tomato Healthy",
        "Healthy tomato foliage featuring uniform deep green pinnate leaves, sturdy stems, active flowering, and absence of blight or viral curling.",
        [
            ("Uniform deep green foliage", "Vibrant, evenly colored leaves without yellowing, necrotic spotting, or mosaic mottling."),
            ("Sturdy erect growth", "Strong central stems with active apical growth and healthy flower clusters."),
            ("Firm turgid leaf texture", "Normal leaf turgor without wilting, cupping, or chlorotic halos.")
        ],
        [
            ("Optimal tomato culture", "Adequate sunlight, balanced nitrogen-phosphorus-potassium feeding, and regular drip irrigation.")
        ],
        [
            ("Standard crop care", "Cultural management",
             "Maintain balanced drip fertigation, consistent soil moisture, staking, and periodic pruning.",
             "No disease treatment required for healthy tomato plants.",
             "Continue routine scouting.",
             None)
        ],
        [
            ("Routine scouting", "Scout tomato plants twice weekly for early signs of hornworms, whiteflies, or blight."),
            ("Mulching and staking", "Keep plants staked and ground mulched to prevent soil splash and maintain airflow.")
        ]
    ),
]


def run_migration():
    print("Connecting to PostgreSQL database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Step 1: Ensure prediction_key column exists on diseases
        print("1. Checking 'prediction_key' column on diseases table...")
        cur.execute("""
            ALTER TABLE diseases
            ADD COLUMN IF NOT EXISTS prediction_key VARCHAR(100);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_diseases_prediction_key
            ON diseases(prediction_key);
        """)
        conn.commit()
        print("   'prediction_key' column and index ready.")

        # Step 2: Update the 5 existing diseases with their prediction_key
        print("2. Mapping existing 5 diseases to their prediction_key...")
        existing_updates = [
            (1, "Tomato___Late_blight"),
            (2, "Tomato___Early_blight"),
            (3, "Tomato___Leaf_Mold"),
            (4, "Potato___Late_blight"),
            (5, "Potato___Early_blight"),
        ]
        for disease_id, pkey in existing_updates:
            cur.execute("""
                UPDATE diseases
                SET prediction_key = %s
                WHERE id = %s AND (prediction_key IS NULL OR prediction_key != %s);
            """, (pkey, disease_id, pkey))
        conn.commit()
        print("   Existing 5 diseases updated.")

        # Step 3: Seed missing crops
        print("3. Seeding missing crops...")
        for name, sci_name, desc in CROPS_DATA:
            cur.execute("SELECT id FROM crops WHERE name = %s;", (name,))
            row = cur.fetchone()
            if not row:
                cur.execute("""
                    INSERT INTO crops (name, scientific_name, description, created_at)
                    VALUES (%s, %s, %s, NOW());
                """, (name, sci_name, desc))
                print(f"   Inserted crop: {name}")
        conn.commit()

        # Build crop name to id mapping
        cur.execute("SELECT id, name FROM crops;")
        crop_name_to_id = {row[1]: row[0] for row in cur.fetchall()}

        # Helper to get or insert symptom
        def get_or_create_symptom(name, desc):
            cur.execute("SELECT id FROM symptoms WHERE name = %s;", (name,))
            res = cur.fetchone()
            if res:
                return res[0]
            cur.execute(
                "INSERT INTO symptoms (name, description) VALUES (%s, %s) RETURNING id;",
                (name, desc)
            )
            return cur.fetchone()[0]

        # Helper to get or insert cause
        def get_or_create_cause(name, desc):
            cur.execute("SELECT id FROM causes WHERE name = %s;", (name,))
            res = cur.fetchone()
            if res:
                return res[0]
            cur.execute(
                "INSERT INTO causes (name, description) VALUES (%s, %s) RETURNING id;",
                (name, desc)
            )
            return cur.fetchone()[0]

        # Helper to get or insert prevention
        def get_or_create_prevention(title, desc):
            cur.execute("SELECT id FROM prevention WHERE title = %s;", (title,))
            res = cur.fetchone()
            if res:
                return res[0]
            cur.execute(
                "INSERT INTO prevention (title, description) VALUES (%s, %s) RETURNING id;",
                (title, desc)
            )
            return cur.fetchone()[0]

        # Step 4: Seed all 38 classes
        print("4. Seeding knowledge base for all 38 classes...")
        seeded_count = 0
        updated_count = 0

        for item in KNOWLEDGE_BASE:
            pkey, crop_name, disease_name, description, symptoms, causes, treatments, prev_list = item
            crop_id = crop_name_to_id.get(crop_name)
            if not crop_id:
                print(f"   ⚠️ Crop {crop_name} not found! Skipping {pkey}")
                continue

            # Check if disease already exists by prediction_key
            cur.execute("SELECT id FROM diseases WHERE prediction_key = %s;", (pkey,))
            existing = cur.fetchone()

            if existing:
                disease_id = existing[0]
                # Update description
                cur.execute("""
                    UPDATE diseases
                    SET description = %s, name = %s, crop_id = %s
                    WHERE id = %s;
                """, (description, disease_name, crop_id, disease_id))
                updated_count += 1
            else:
                cur.execute("""
                    INSERT INTO diseases (crop_id, name, description, prediction_key, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING id;
                """, (crop_id, disease_name, description, pkey))
                disease_id = cur.fetchone()[0]
                seeded_count += 1

            # Connect symptoms
            for s_name, s_desc in symptoms:
                sym_id = get_or_create_symptom(s_name, s_desc)
                cur.execute("""
                    INSERT INTO disease_symptoms (disease_id, symptom_id)
                    SELECT %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM disease_symptoms WHERE disease_id = %s AND symptom_id = %s
                    );
                """, (disease_id, sym_id, disease_id, sym_id))

            # Connect causes
            for c_name, c_desc in causes:
                cause_id = get_or_create_cause(c_name, c_desc)
                cur.execute("""
                    INSERT INTO disease_causes (disease_id, cause_id)
                    SELECT %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM disease_causes WHERE disease_id = %s AND cause_id = %s
                    );
                """, (disease_id, cause_id, disease_id, cause_id))

            # Connect prevention
            for p_title, p_desc in prev_list:
                prev_id = get_or_create_prevention(p_title, p_desc)
                cur.execute("""
                    INSERT INTO disease_prevention (disease_id, prevention_id)
                    SELECT %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM disease_prevention WHERE disease_id = %s AND prevention_id = %s
                    );
                """, (disease_id, prev_id, disease_id, prev_id))

            # Insert treatments and application rates if not already existing
            for t_item in treatments:
                t_name, t_type, t_desc, t_instr, t_prec, rate_info = t_item
                cur.execute("""
                    SELECT id FROM treatments
                    WHERE disease_id = %s AND name = %s;
                """, (disease_id, t_name))
                t_existing = cur.fetchone()

                if t_existing:
                    treatment_id = t_existing[0]
                else:
                    cur.execute("""
                        INSERT INTO treatments (disease_id, name, type, description, instructions, precautions, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        RETURNING id;
                    """, (disease_id, t_name, t_type, t_desc, t_instr, t_prec))
                    treatment_id = cur.fetchone()[0]

                if rate_info:
                    method, unit, rate, basis, notes = rate_info
                    cur.execute("""
                        SELECT id FROM application_rates
                        WHERE treatment_id = %s AND measurement_unit = %s;
                    """, (treatment_id, unit))
                    if not cur.fetchone():
                        cur.execute("""
                            INSERT INTO application_rates (treatment_id, application_method, measurement_unit, rate, basis, notes)
                            VALUES (%s, %s, %s, %s, %s, %s);
                        """, (treatment_id, method, unit, rate, basis, notes))

        conn.commit()
        print(f"5. Seeding complete! Inserted: {seeded_count}, Updated: {updated_count}.")

        # Step 5: Verification check
        cur.execute("SELECT count(*) FROM crops;")
        print(f"   Total crops in DB: {cur.fetchone()[0]}")
        cur.execute("SELECT count(*) FROM diseases WHERE prediction_key IS NOT NULL;")
        print(f"   Diseases with prediction_key: {cur.fetchone()[0]} / 38")

    except Exception as e:
        conn.rollback()
        print("❌ Error during seeding:", e)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
