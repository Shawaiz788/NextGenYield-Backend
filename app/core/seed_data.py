"""
backend/app/core/seed_data.py
Idempotent database seeder for deterministic agronomic advisory rules and peer showcases.
Supports both PostgreSQL (Supabase) and SQLite without unique constraint violations.
"""
from datetime import date
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models.advisory import AgronomicAdvisoryRule, PeerShowcaseField
from app.models.user import User
from app.models.machinery import MachineryListing
from app.models.marketplace import MarketplaceItem
from app.models.community import CommunityPost
from app.models.field import Field

logger = logging.getLogger("NextGenYield:Seed")

ADVISORY_RULES_SEED = [
    {
        "rule_id": "rule_stage_0",
        "stage_index": 0,
        "stage_name": "Tillering",
        "summary_text_en": "Tillering Stage: Crown root establishment and secondary shoot emergence.",
        "summary_text_ur": "شاخیں نکلنے کا مرحلہ: جڑوں کی مضبوطی اور پودے سے نئی شاخیں نکلنے کا وقت۔",
        "irrigation_advice_en": "Apply 1st critical irrigation at Crown Root Initiation (CRI) 20-25 days after sowing.",
        "irrigation_advice_ur": "بوائی کے 20 سے 25 دن بعد کور کا پہلا پانی ضرور لگائیں۔",
        "nutrient_advice_en": "Broadcast 1st topdress Urea (50 kg/acre) immediately before or with irrigation.",
        "nutrient_advice_ur": "پہلے پانی کے ساتھ ایک بوری یوریا فی ایکڑ چھٹہ کریں۔",
        "risk_alerts": [
            {"type": "weed", "title": "Broadleaf Weed Hazard", "desc": "Check for Bathu and Lehli weeds; apply selective post-emergence herbicide if needed."}
        ],
        "audio_script_ur": "بوائی کے بیس سے پچیس دن بعد کور کا پہلا پانی لگائیں اور ساتھ ایک بوری یوریا چھٹہ کریں۔ چوڑے پتے والی جڑی بوٹیوں کا تدارک کریں۔"
    },
    {
        "rule_id": "rule_stage_1",
        "stage_index": 1,
        "stage_name": "Jointing",
        "summary_text_en": "Jointing Stage: Rapid stem elongation and node formation.",
        "summary_text_ur": "گولی بننے کا مرحلہ: نالی بننے اور تنے کی تیز رفتار لمبائی کا مرحلہ۔",
        "irrigation_advice_en": "Ensure adequate soil moisture; apply 2nd irrigation 45-50 DAS.",
        "irrigation_advice_ur": "بوائی کے 45 سے 50 دن بعد دوسرا پانی لگائیں تاکہ تنے کی لمبائی متاثر نہ ہو۔",
        "nutrient_advice_en": "Apply remaining split dose of Nitrogen and Zinc Sulphate.",
        "nutrient_advice_ur": "بقیہ یوریا کھاد اور زنک سلفیٹ کا چھٹہ کریں۔",
        "risk_alerts": [
            {"type": "nutrient", "title": "Nitrogen Deficiency", "desc": "Yellowing of lower leaves indicates nitrogen deficiency."}
        ],
        "audio_script_ur": "گولی بننے کے مرحلے پر دوسرا پانی لگائیں اور بقیہ یوریا اور زنک کا استعمال مکمل کریں۔"
    },
    {
        "rule_id": "rule_stage_2",
        "stage_index": 2,
        "stage_name": "Booting",
        "summary_text_en": "Booting Stage: Inflorescence head swollen inside the flag leaf sheath.",
        "summary_text_ur": "گوبھ کا مرحلہ: سٹہ بننے اور جھنڈا پتے کے اندر پھولنے کا انتہائی اہم مرحلہ۔",
        "irrigation_advice_en": "Critical water requirement! Avoid moisture stress during spikelet development.",
        "irrigation_advice_ur": "پانی کی اشد ضرورت ہے۔ اس مرحلے پر زمین میں نمی کی کمی ہرگز نہ آنے دیں۔",
        "nutrient_advice_en": "Foliar spray of Potassium and Boron to boost spikelet fertility.",
        "nutrient_advice_ur": "سٹے میں دانوں کی زرخیزی کے لیے پوٹاش اور بوران کا سپرے کریں۔",
        "risk_alerts": [
            {"type": "rust", "title": "Stripe Rust Warning", "desc": "Cool humid winds favor Yellow Stripe Rust. Inspect lower leaves."}
        ],
        "audio_script_ur": "گوبھ کے مرحلے پر فصل کو سوکا نہ لگنے دیں۔ زرد کنگی کا معائنہ کریں اور احتیاطی سپرے کریں۔"
    },
    {
        "rule_id": "rule_stage_3",
        "stage_index": 3,
        "stage_name": "Flowering / Anthesis",
        "summary_text_en": "Anthesis / Flowering Stage: Delicate yellow anthers shed pollen.",
        "summary_text_ur": "پھول یا بور کا مرحلہ: سٹوں سے زرد دانوں کے بور نکلنے کا وقت۔",
        "irrigation_advice_en": "Irrigate only in calm weather to prevent crop lodging (falling over).",
        "irrigation_advice_ur": "ہوا بند ہونے کی صورت میں ہلکا پانی لگائیں تاکہ فصل گرنے سے محفوظ رہے۔",
        "nutrient_advice_en": "Do not disturb canopy; avoid pesticide sprays during peak morning pollination.",
        "nutrient_advice_ur": "صبح کے وقت پولینیشن کے دوران کیڑے مار ادویات کا سپرے نہ کریں۔",
        "risk_alerts": [
            {"type": "weather", "title": "Lodging Risk", "desc": "High wind gusts accompanied by heavy watering will cause crop lodging."}
        ],
        "audio_script_ur": "بور کے وقت تیز ہوا میں پانی نہ لگائیں تاکہ فصل نہ گرے۔ صبح کے وقت سپرے سے گریز کریں۔"
    },
    {
        "rule_id": "rule_stage_4",
        "stage_index": 4,
        "stage_name": "Grain Filling",
        "summary_text_en": "Grain Filling Stage: Milky to soft-dough carbohydrate translocation.",
        "summary_text_ur": "دودھیا اور دانہ بننے کا مرحلہ: دانے میں دودھ اور نشاستہ بھرنے کا عمل۔",
        "irrigation_advice_en": "Apply final light irrigation to prevent premature kernel shriveling.",
        "irrigation_advice_ur": "آخری ہلکا پانی لگائیں تاکہ گرمی کی وجہ سے دانہ سکڑنے سے بچ سکے۔",
        "nutrient_advice_en": "No soil fertilizer needed. Photosynthetic activity of flag leaf is paramount.",
        "nutrient_advice_ur": "اب زمین میں کھاد ڈالنے کی ضرورت نہیں، جھنڈا پتے کو تندرست رکھیں۔",
        "risk_alerts": [
            {"type": "aphid", "title": "Aphid (Sust Sula) Alert", "desc": "Check spike heads for green aphid colonies."}
        ],
        "audio_script_ur": "دانہ بھرنے کے دوران آخری ہلکا پانی دیں تاکہ دانہ موٹا اور وزنی بنے۔ سست تیلے کا معائنہ کریں۔"
    },
    {
        "rule_id": "rule_stage_5",
        "stage_index": 5,
        "stage_name": "Maturity",
        "summary_text_en": "Maturity & Ripening: Golden canopy with hard kernel (<12% moisture).",
        "summary_text_ur": "پکائی اور کٹائی کا مرحلہ: سنہری فصل اور دانہ سخت ہونے کی نشانی۔",
        "irrigation_advice_en": "Stop all irrigation completely 15-20 days before combine harvesting.",
        "irrigation_advice_ur": "کٹائی سے 15 سے 20 دن قبل پانی مکمل طور پر بند کر دیں۔",
        "nutrient_advice_en": "Cease all inputs. Prepare combine harvester and storage grain bags.",
        "nutrient_advice_ur": "کھاد اور ادویات کا استعمال ختم کریں۔ کٹائی اور گودام کی تیاری کریں۔",
        "risk_alerts": [
            {"type": "harvest", "title": "Pre-Harvest Shattering", "desc": "Harvest promptly when grain moisture reaches 12-14%."}
        ],
        "audio_script_ur": "کٹائی سے پندرہ دن پہلے پانی بند کر دیں۔ دانہ خشک ہونے پر وقت پر کٹائی مکمل کریں۔"
    },
]

SHOWCASE_FIELDS_SEED = [
    {
        "showcase_id": "sc_01",
        "field_code": "PK-FSD-01",
        "district": "Faisalabad / Chak 214-RB",
        "wheat_variety": "Akbar-2019",
        "seed_company": "Punjab Seed Corporation (PSC)",
        "fertilizer_company": "Fauji Fertilizer Company (FFC)",
        "area_acres": 12.5,
        "shape_type": "rectangle",
        "yield_maunds_per_acre": 61.8,
        "yield_kg_sqm": 0.62,
        "sowing_date": date(2025, 11, 10),
        "harvest_date": date(2026, 4, 1),
        "cycle_event_log": [
            {"day": 0, "event": "Drill sowing @ 50kg/acre with 1 Bag DAP"},
            {"day": 22, "event": "1st irrigation with 1 Bag Urea"},
            {"day": 45, "event": "Broadleaf weed spray (Bromoxynil)"},
            {"day": 52, "event": "2nd irrigation with 0.5 Bag Urea + Zinc"},
            {"day": 78, "event": "Booting irrigation + Foliar Potash spray"},
            {"day": 96, "event": "Anthesis monitoring; no lodging observed"},
            {"day": 118, "event": "Final milk-stage light watering"},
            {"day": 142, "event": "Combine harvested @ 61.8 Maunds/Acre"}
        ]
    },
    {
        "showcase_id": "sc_02",
        "field_code": "PK-LHR-03",
        "district": "Lahore / Manga Mandi",
        "wheat_variety": "Dilkash-20",
        "seed_company": "Ayub Agricultural Research Institute",
        "fertilizer_company": "Engro Fertilizers",
        "area_acres": 8.0,
        "shape_type": "square",
        "yield_maunds_per_acre": 58.4,
        "yield_kg_sqm": 0.58,
        "sowing_date": date(2025, 11, 15),
        "harvest_date": date(2026, 4, 5),
        "cycle_event_log": [
            {"day": 0, "event": "Bed planting with Engro Zorawar (DAP)"},
            {"day": 21, "event": "1st irrigation with Engro Urea"},
            {"day": 75, "event": "Booting check; zero rust infestation"},
            {"day": 140, "event": "Harvested @ 58.4 Maunds/Acre"}
        ]
    },
]

def seed_advisory_rules(db: Session) -> int:
    """Upsert canonical advisory rules idempotently by rule_id or stage_index."""
    upserted = 0
    for data in ADVISORY_RULES_SEED:
        existing = db.query(AgronomicAdvisoryRule).filter(
            (AgronomicAdvisoryRule.rule_id == data["rule_id"]) | 
            (AgronomicAdvisoryRule.stage_index == data["stage_index"])
        ).first()
        if existing:
            for key, val in data.items():
                setattr(existing, key, val)
        else:
            rule = AgronomicAdvisoryRule(**data)
            db.add(rule)
        upserted += 1
    db.commit()
    return upserted

def seed_showcase_fields(db: Session) -> int:
    """Upsert benchmark showcase fields idempotently by showcase_id or field_code."""
    upserted = 0
    for data in SHOWCASE_FIELDS_SEED:
        existing = db.query(PeerShowcaseField).filter(
            (PeerShowcaseField.showcase_id == data["showcase_id"]) |
            (PeerShowcaseField.field_code == data["field_code"])
        ).first()
        if existing:
            for key, val in data.items():
                setattr(existing, key, val)
        else:
            sc = PeerShowcaseField(**data)
            db.add(sc)
        upserted += 1
    db.commit()
    return upserted

def seed_community_machinery_marketplace(db: Session):
    """Seed sample machinery rentals, marketplace listings, and community posts."""
    # Ensure demo seed user exists
    demo_user = db.query(User).filter(User.phone_number == "03001234567").first()
    if not demo_user:
        demo_user = User(
            user_id="usr_punjab_agri_demo",
            full_name="Chaudhry Riaz Agri",
            phone_number="03001234567",
            password_hash="$2b$12$eXoG1qfVpY8M9kX5s3BZe.9/J5s7u9X3B5/oV6c2aJ8yG9x2/d6k2",
            role="farmer",
            district="Faisalabad",
            language_pref="en"
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)

    # Seed Machinery Listings
    mach_items = [
        {
            "machinery_id": "mach_seed_01",
            "owner_id": demo_user.user_id,
            "title": "Millat MF-385 (85 HP) + Laser Land Leveler",
            "machinery_type": "laser_leveler",
            "brand_model": "Massey Ferguson 385 (Millat)",
            "horsepower": 85.0,
            "hourly_rate_pkr": 2500.0,
            "daily_rate_pkr": 18000.0,
            "district": "Faisalabad",
            "location_address": "Samundri Road, Near Grain Market",
            "contact_phone": "03001234567",
            "description": "High precision dual-slope laser transmitter with hydraulic scraper bucket. Ideal for wheat field pre-sowing leveling.",
            "image_url": "https://images.unsplash.com/photo-1592982537447-7440770cbfc9?w=600",
            "is_available": True,
        },
        {
            "machinery_id": "mach_seed_02",
            "owner_id": demo_user.user_id,
            "title": "Al-Ghazi New Holland 640 + Heavy Rotavator",
            "machinery_type": "rotavator",
            "brand_model": "New Holland 640 (75 HP)",
            "horsepower": 75.0,
            "hourly_rate_pkr": 2000.0,
            "daily_rate_pkr": 14000.0,
            "district": "Sheikhupura",
            "location_address": "Chuharkana Tehsil, Sheikhupura",
            "contact_phone": "03007654321",
            "description": "48-blade rotary tiller for fine seedbed preparation after Rauni watering. Pulverizes heavy clods effectively.",
            "image_url": "https://images.unsplash.com/photo-1589923188900-85dae523342b?w=600",
            "is_available": True,
        },
        {
            "machinery_id": "mach_seed_03",
            "owner_id": demo_user.user_id,
            "title": "Automatic 11-Row Wheat Seed Drill (Rabi Sowing)",
            "machinery_type": "seed_drill",
            "brand_model": "Punjab Agri Tools Drill",
            "horsepower": 50.0,
            "hourly_rate_pkr": 1200.0,
            "daily_rate_pkr": 7500.0,
            "district": "Sahiwal",
            "location_address": "Gamber, Sahiwal District",
            "contact_phone": "03019876543",
            "description": "Uniform seed depth (2-3 inches) with fertilizer placement chamber for simultaneous basal DAP drilling.",
            "image_url": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=600",
            "is_available": True,
        }
    ]
    for m in mach_items:
        if not db.query(MachineryListing).filter(MachineryListing.machinery_id == m["machinery_id"]).first():
            db.add(MachineryListing(**m))

    # Seed Community Posts
    posts = [
        {
            "post_id": "post_seed_01",
            "user_id": demo_user.user_id,
            "author_name": demo_user.full_name,
            "author_district": "Faisalabad",
            "category": "agronomy_tips",
            "title": "Optimal Sowing Window for Punjab Wheat 2026",
            "content": "Agronomy advisory: For central Punjab farmers, November 1st to 20th provides the highest tillering potential for Akbar-2019 and Dilkash-20. Sowing delayed past Nov 30 reduces yield by 1% per day due to terminal heat stress during grain filling.",
            "image_url": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=600",
            "likes_count": 14,
            "comments_count": 3
        },
        {
            "post_id": "post_seed_02",
            "user_id": demo_user.user_id,
            "author_name": "Malik Usman",
            "author_district": "Sheikhupura",
            "category": "machinery",
            "title": "Laser Land Leveling Experience Before Sowing",
            "content": "Laser leveled our 15-acre plot before Rauni watering this season. Saved nearly 35% tube-well diesel cost and water coverage was completely uniform across all corners. Highly recommend hiring a laser leveler!",
            "image_url": "https://images.unsplash.com/photo-1592982537447-7440770cbfc9?w=600",
            "likes_count": 22,
            "comments_count": 5
        }
    ]
    for p in posts:
        if not db.query(CommunityPost).filter(CommunityPost.post_id == p["post_id"]).first():
            db.add(CommunityPost(**p))

    # Seed Marketplace Items
    market_items = [
        {
            "item_id": "mkt_seed_01",
            "seller_id": demo_user.user_id,
            "seller_name": demo_user.full_name,
            "seller_phone": "03001234567",
            "title": "Certified Akbar-2019 Wheat Seed (50 kg Bag)",
            "category": "seeds",
            "price_pkr": 4850.0,
            "condition": "new",
            "district": "Faisalabad",
            "location_address": "Punjab Seed Corp Authorized Depot, Jhang Road",
            "description": "Graded, treated with fungicide, certified germination rate >90%. Ideal for irrigated areas.",
            "image_url": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600",
            "is_sold": False,
        },
        {
            "item_id": "mkt_seed_02",
            "seller_id": demo_user.user_id,
            "seller_name": demo_user.full_name,
            "seller_phone": "03001234567",
            "title": "Engro DAP Di-Ammonium Phosphate (50 kg)",
            "category": "fertilizer",
            "price_pkr": 14300.0,
            "condition": "new",
            "district": "Faisalabad",
            "location_address": "Grain Market, Shop #12",
            "description": "Original sealed bags with subsidy barcode. High phosphorus (46% P2O5, 18% N) for strong basal root establishment.",
            "image_url": "https://images.unsplash.com/photo-1585314062340-f1a5a7c9328d?w=600",
            "is_sold": False,
        },
        {
            "item_id": "mkt_seed_03",
            "seller_id": demo_user.user_id,
            "seller_name": "Tariq Mahmood",
            "seller_phone": "03023456789",
            "title": "Top Grade Milling Wheat (100 Maunds Available)",
            "category": "wheat_grain",
            "price_pkr": 3950.0,
            "condition": "new",
            "district": "Sargodha",
            "location_address": "Bhalwal Mandi, Sargodha",
            "description": "Clean, sun-dried grain, moisture level <11.5%. Harvested April 2026, stored in fumigated silo bags.",
            "image_url": "https://images.unsplash.com/photo-1543257580-7269da773bf5?w=600",
            "is_sold": False,
        }
    ]
    for itm in market_items:
        if not db.query(MarketplaceItem).filter(MarketplaceItem.item_id == itm["item_id"]).first():
            db.add(MarketplaceItem(**itm))

    db.commit()

def seed_community_fields(db: Session):
    """Ensure community demo farmers have demarcated fields with coordinates on the Leaflet map."""
    demo_user = db.query(User).filter(User.phone_number == "03001234567").first()
    if not demo_user:
        return

    sample_parcels = [
        {
            "field_id": "fld_seed_comm_01",
            "field_code": "PK-FSD-C1",
            "user_id": demo_user.user_id,
            "field_name": "Canal Block North",
            "shape_type": "polygon",
            "area_acres": 12.5,
            "area_sqm": 50585.7,
            "center_latitude": 31.4225,
            "center_longitude": 73.0755,
            "boundary_geojson": {
                "type": "Polygon",
                "coordinates": [[
                    [73.0735, 31.4210],
                    [73.0775, 31.4210],
                    [73.0775, 31.4240],
                    [73.0735, 31.4240],
                    [73.0735, 31.4210]
                ]],
                "properties": {"soil_texture": "Sandy Loam"}
            }
        },
        {
            "field_id": "fld_seed_comm_02",
            "field_code": "PK-FSD-C2",
            "user_id": demo_user.user_id,
            "field_name": "Chak 204 South Plot",
            "shape_type": "polygon",
            "area_acres": 8.0,
            "area_sqm": 32374.8,
            "center_latitude": 31.4150,
            "center_longitude": 73.0825,
            "boundary_geojson": {
                "type": "Polygon",
                "coordinates": [[
                    [73.0805, 31.4135],
                    [73.0845, 31.4135],
                    [73.0845, 31.4165],
                    [73.0805, 31.4165],
                    [73.0805, 31.4135]
                ]],
                "properties": {"soil_texture": "Clay Loam"}
            }
        }
    ]

    for p in sample_parcels:
        if not db.query(Field).filter(Field.field_id == p["field_id"]).first():
            db.add(Field(**p))

    db.commit()

def seed():
    """Execute schema creation and idempotent seed data population."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        rules_count = seed_advisory_rules(db)
        showcase_count = seed_showcase_fields(db)
        seed_community_machinery_marketplace(db)
        seed_community_fields(db)
        logger.info(f"Database seeded successfully: {rules_count} advisory rules, {showcase_count} showcase fields.")
    except Exception as e:
        db.rollback()
        logger.warning(f"Seeding encountered notice (non-fatal): {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
