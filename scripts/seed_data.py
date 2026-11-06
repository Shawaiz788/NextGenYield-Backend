from app.database import SessionLocal, Base, engine
from app.models.advisory import AgronomicAdvisoryRule, PeerShowcaseField
from datetime import date

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if rules already seeded
        if db.query(AgronomicAdvisoryRule).count() == 0:
            print("Seeding deterministic agronomic advisory rules...")
            rules = [
                AgronomicAdvisoryRule(
                    rule_id="rule_stage_0",
                    stage_index=0,
                    stage_name="Tillering",
                    summary_text_en="Tillering Stage: Crown root establishment and secondary shoot emergence.",
                    summary_text_ur="شاخیں نکلنے کا مرحلہ: جڑوں کی مضبوطی اور پودے سے نئی شاخیں نکلنے کا وقت۔",
                    irrigation_advice_en="Apply 1st critical irrigation at Crown Root Initiation (CRI) 20-25 days after sowing.",
                    irrigation_advice_ur="بوائی کے 20 سے 25 دن بعد کور کا پہلا پانی ضرور لگائیں۔",
                    nutrient_advice_en="Broadcast 1st topdress Urea (50 kg/acre) immediately before or with irrigation.",
                    nutrient_advice_ur="پہلے پانی کے ساتھ ایک بوری یوریا فی ایکڑ چھٹہ کریں۔",
                    risk_alerts=[
                        {"type": "weed", "title": "Broadleaf Weed Hazard", "desc": "Check for Bathu and Lehli weeds; apply selective post-emergence herbicide if needed."}
                    ],
                    audio_script_ur="بوائی کے بیس سے پچیس دن بعد کور کا پہلا پانی لگائیں اور ساتھ ایک بوری یوریا چھٹہ کریں۔ چوڑے پتے والی جڑی بوٹیوں کا تدارک کریں۔"
                ),
                AgronomicAdvisoryRule(
                    rule_id="rule_stage_1",
                    stage_index=1,
                    stage_name="Jointing",
                    summary_text_en="Jointing Stage: Rapid stem elongation and node formation.",
                    summary_text_ur="گولی بننے کا مرحلہ: نالی بننے اور تنے کی تیز رفتار لمبائی کا مرحلہ۔",
                    irrigation_advice_en="Ensure adequate soil moisture; apply 2nd irrigation 45-50 DAS.",
                    irrigation_advice_ur="بوائی کے 45 سے 50 دن بعد دوسرا پانی لگائیں تاکہ تنے کی لمبائی متاثر نہ ہو۔",
                    nutrient_advice_en="Apply remaining split dose of Nitrogen and Zinc Sulphate.",
                    nutrient_advice_ur="بقیہ یوریا کھاد اور زنک سلفیٹ کا چھٹہ کریں۔",
                    risk_alerts=[
                        {"type": "nutrient", "title": "Nitrogen Deficiency", "desc": "Yellowing of lower leaves indicates nitrogen deficiency."}
                    ],
                    audio_script_ur="گولی بننے کے مرحلے پر دوسرا پانی لگائیں اور بقیہ یوریا اور زنک کا استعمال مکمل کریں۔"
                ),
                AgronomicAdvisoryRule(
                    rule_id="rule_stage_2",
                    stage_index=2,
                    stage_name="Booting",
                    summary_text_en="Booting Stage: Inflorescence head swollen inside the flag leaf sheath.",
                    summary_text_ur="گوبھ کا مرحلہ: سٹہ بننے اور جھنڈا پتے کے اندر پھولنے کا انتہائی اہم مرحلہ۔",
                    irrigation_advice_en="Critical water requirement! Avoid moisture stress during spikelet development.",
                    irrigation_advice_ur="پانی کی اشد ضرورت ہے۔ اس مرحلے پر زمین میں نمی کی کمی ہرگز نہ آنے دیں۔",
                    nutrient_advice_en="Foliar spray of Potassium and Boron to boost spikelet fertility.",
                    nutrient_advice_ur="سٹے میں دانوں کی زرخیزی کے لیے پوٹاش اور بوران کا سپرے کریں۔",
                    risk_alerts=[
                        {"type": "rust", "title": "Stripe Rust Warning", "desc": "Cool humid winds favor Yellow Stripe Rust. Inspect lower leaves."}
                    ],
                    audio_script_ur="گوبھ کے مرحلے پر فصل کو سوکا نہ لگنے دیں۔ زرد کنگی کا معائنہ کریں اور احتیاطی سپرے کریں۔"
                ),
                AgronomicAdvisoryRule(
                    rule_id="rule_stage_3",
                    stage_index=3,
                    stage_name="Flowering / Anthesis",
                    summary_text_en="Anthesis / Flowering Stage: Delicate yellow anthers shed pollen.",
                    summary_text_ur="پھول یا بور کا مرحلہ: سٹوں سے زرد دانوں کے بور نکلنے کا وقت۔",
                    irrigation_advice_en="Irrigate only in calm weather to prevent crop lodging (falling over).",
                    irrigation_advice_ur="ہوا بند ہونے کی صورت میں ہلکا پانی لگائیں تاکہ فصل گرنے سے محفوظ رہے۔",
                    nutrient_advice_en="Do not disturb canopy; avoid pesticide sprays during peak morning pollination.",
                    nutrient_advice_ur="صبح کے وقت پولینیشن کے دوران کیڑے مار ادویات کا سپرے نہ کریں۔",
                    risk_alerts=[
                        {"type": "weather", "title": "Lodging Risk", "desc": "High wind gusts accompanied by heavy watering will cause crop lodging."}
                    ],
                    audio_script_ur="بور کے وقت تیز ہوا میں پانی نہ لگائیں تاکہ فصل نہ گرے۔ صبح کے وقت سپرے سے گریز کریں۔"
                ),
                AgronomicAdvisoryRule(
                    rule_id="rule_stage_4",
                    stage_index=4,
                    stage_name="Grain Filling",
                    summary_text_en="Grain Filling Stage: Milky to soft-dough carbohydrate translocation.",
                    summary_text_ur="دودھیا اور دانہ بننے کا مرحلہ: دانے میں دودھ اور نشاستہ بھرنے کا عمل۔",
                    irrigation_advice_en="Apply final light irrigation to prevent premature kernel shriveling.",
                    irrigation_advice_ur="آخری ہلکا پانی لگائیں تاکہ گرمی کی وجہ سے دانہ سکڑنے سے بچ سکے۔",
                    nutrient_advice_en="No soil fertilizer needed. Photosynthetic activity of flag leaf is paramount.",
                    nutrient_advice_ur="اب زمین میں کھاد ڈالنے کی ضرورت نہیں، جھنڈا پتے کو تندرست رکھیں۔",
                    risk_alerts=[
                        {"type": "aphid", "title": "Aphid (Sust Sula) Alert", "desc": "Check spike heads for green aphid colonies."}
                    ],
                    audio_script_ur="دانہ بھرنے کے دوران آخری ہلکا پانی دیں تاکہ دانہ موٹا اور وزنی بنے۔ سست تیلے کا معائنہ کریں۔"
                ),
                AgronomicAdvisoryRule(
                    rule_id="rule_stage_5",
                    stage_index=5,
                    stage_name="Maturity",
                    summary_text_en="Maturity & Ripening: Golden canopy with hard kernel (<12% moisture).",
                    summary_text_ur="پکائی اور کٹائی کا مرحلہ: سنہری فصل اور دانہ سخت ہونے کی نشانی۔",
                    irrigation_advice_en="Stop all irrigation completely 15-20 days before combine harvesting.",
                    irrigation_advice_ur="کٹائی سے 15 سے 20 دن قبل پانی مکمل طور پر بند کر دیں۔",
                    nutrient_advice_en="Cease all inputs. Prepare combine harvester and storage grain bags.",
                    nutrient_advice_ur="کھاد اور ادویات کا استعمال ختم کریں۔ کٹائی اور گودام کی تیاری کریں۔",
                    risk_alerts=[
                        {"type": "harvest", "title": "Pre-Harvest Shattering", "desc": "Harvest promptly when grain moisture reaches 12-14%."}
                    ],
                    audio_script_ur="کٹائی سے پندرہ دن پہلے پانی بند کر دیں۔ دانہ خشک ہونے پر وقت پر کٹائی مکمل کریں۔"
                ),
            ]
            db.bulk_save_objects(rules)
            db.commit()
            print("Successfully seeded agronomic advisory rules.")

        # Check if benchmark showcase fields already seeded
        if db.query(PeerShowcaseField).count() == 0:
            print("Seeding verified peer showcase fields...")
            showcase_fields = [
                PeerShowcaseField(
                    showcase_id="sc_01",
                    field_code="PK-FSD-01",
                    district="Faisalabad / Chak 214-RB",
                    wheat_variety="Akbar-2019",
                    seed_company="Punjab Seed Corporation (PSC)",
                    fertilizer_company="Fauji Fertilizer Company (FFC)",
                    area_acres=12.5,
                    shape_type="rectangle",
                    yield_maunds_per_acre=61.8,
                    yield_kg_sqm=0.618,
                    sowing_date=date(2025, 11, 10),
                    harvest_date=date(2026, 4, 1),
                    cycle_event_log=[
                        {"day": 0, "event": "Drill sowing @ 50kg/acre with 1 Bag DAP"},
                        {"day": 22, "event": "1st irrigation with 1 Bag Urea"},
                        {"day": 45, "event": "Broadleaf weed spray (Bromoxynil)"},
                        {"day": 52, "event": "2nd irrigation with 0.5 Bag Urea + Zinc"},
                        {"day": 78, "event": "Booting irrigation + Foliar Potash spray"},
                        {"day": 96, "event": "Anthesis monitoring; no lodging observed"},
                        {"day": 118, "event": "Final milk-stage light watering"},
                        {"day": 142, "event": "Combine harvested @ 61.8 Maunds/Acre"}
                    ]
                ),
                PeerShowcaseField(
                    showcase_id="sc_02",
                    field_code="PK-LHR-03",
                    district="Lahore / Manga Mandi",
                    wheat_variety="Dilkash-20",
                    seed_company="Ayub Agricultural Research Institute",
                    fertilizer_company="Engro Fertilizers",
                    area_acres=8.0,
                    shape_type="square",
                    yield_maunds_per_acre=58.4,
                    yield_kg_sqm=0.584,
                    sowing_date=date(2025, 11, 15),
                    harvest_date=date(2026, 4, 5),
                    cycle_event_log=[
                        {"day": 0, "event": "Bed planting with Engro Zorawar (DAP)"},
                        {"day": 21, "event": "1st irrigation with Engro Urea"},
                        {"day": 75, "event": "Booting check; zero rust infestation"},
                        {"day": 140, "event": "Harvested @ 58.4 Maunds/Acre"}
                    ]
                ),
            ]
            db.bulk_save_objects(showcase_fields)
            db.commit()
            print("Successfully seeded peer showcase fields.")

    finally:
        db.close()

if __name__ == "__main__":
    seed()

