"""Generate 200 diverse patient reports for ER decision support testing.

Profiles alternate between:
- Author: senior physician vs R1 resident
- Style: expressive vs concise/non-communicative
- Priority: 1 (critical) to 5 (non-urgent)
"""

import argparse
import random
from collections import Counter
from pathlib import Path

CONDITIONS = [
    # Critical (Priority 1)
    {"name": "STEMI", "priority": 1, "template": "chest_pain_stemi"},
    {"name": "Cardiac Arrest", "priority": 1, "template": "cardiac_arrest"},
    {"name": "Severe Sepsis", "priority": 1, "template": "severe_sepsis"},
    {"name": "Intracranial Hemorrhage", "priority": 1, "template": "ich"},
    {"name": "Tension Pneumothorax", "priority": 1, "template": "tension_pneumo"},
    {"name": "Anaphylaxis", "priority": 1, "template": "anaphylaxis"},
    {"name": "DKA Severe", "priority": 1, "template": "dka_severe"},
    {"name": "Massive PE", "priority": 1, "template": "massive_pe"},
    {"name": "Status Epilepticus", "priority": 1, "template": "status_epilepticus"},
    {"name": "Aortic Dissection", "priority": 1, "template": "aortic_dissection"},
    # Urgent (Priority 2)
    {"name": "NSTEMI", "priority": 2, "template": "nstemi"},
    {"name": "Stroke (CVA)", "priority": 2, "template": "stroke"},
    {"name": "Pneumonia Severe", "priority": 2, "template": "pneumonia_severe"},
    {"name": "GI Bleed", "priority": 2, "template": "gi_bleed"},
    {"name": "Pyelonephritis", "priority": 2, "template": "pyelo"},
    {"name": "COPD Exacerbation", "priority": 2, "template": "copd_exac"},
    {"name": "Heart Failure Acute", "priority": 2, "template": "chf_acute"},
    {"name": "Meningitis", "priority": 2, "template": "meningitis"},
    {"name": "Appendicitis", "priority": 2, "template": "appendicitis"},
    {"name": "Ectopic Pregnancy", "priority": 2, "template": "ectopic"},
    # Moderate (Priority 3)
    {"name": "Renal Colic", "priority": 3, "template": "renal_colic"},
    {"name": "Migraine", "priority": 3, "template": "migraine"},
    {"name": "Asthma Moderate", "priority": 3, "template": "asthma_mod"},
    {"name": "UTI", "priority": 3, "template": "uti"},
    {"name": "Cellulitis", "priority": 3, "template": "cellulitis"},
    {"name": "Deep Vein Thrombosis", "priority": 3, "template": "dvt"},
    {"name": "Atrial Fibrillation", "priority": 3, "template": "afib"},
    {"name": "Diverticulitis", "priority": 3, "template": "diverticulitis"},
    {"name": "Cholecystitis", "priority": 3, "template": "cholecystitis"},
    {"name": "Pancreatitis", "priority": 3, "template": "pancreatitis"},
    # Low (Priority 4)
    {"name": "Sprained Ankle", "priority": 4, "template": "sprain"},
    {"name": "Minor Laceration", "priority": 4, "template": "laceration"},
    {"name": "Otitis Media", "priority": 4, "template": "otitis"},
    {"name": "Pharyngitis", "priority": 4, "template": "pharyngitis"},
    {"name": "Conjunctivitis", "priority": 4, "template": "conjunctivitis"},
    {"name": "Minor Allergic Reaction", "priority": 4, "template": "allergy_minor"},
    {"name": "Dermatitis", "priority": 4, "template": "dermatitis"},
    {"name": "Minor Head Injury", "priority": 4, "template": "head_injury_minor"},
    {"name": "Muscle Strain", "priority": 4, "template": "strain"},
    {"name": "Insect Bite", "priority": 4, "template": "insect_bite"},
    # Non-urgent (Priority 5)
    {"name": "Common Cold", "priority": 5, "template": "cold"},
    {"name": "Mild Headache", "priority": 5, "template": "headache_mild"},
    {"name": "Prescription Refill", "priority": 5, "template": "refill"},
    {"name": "Mild Rash", "priority": 5, "template": "rash_mild"},
    {"name": "Sore Throat", "priority": 5, "template": "sore_throat"},
    {"name": "Mild Back Pain", "priority": 5, "template": "back_pain_mild"},
    {"name": "Anxiety Attack", "priority": 5, "template": "anxiety"},
    {"name": "Insomnia", "priority": 5, "template": "insomnia"},
    {"name": "Minor Bruise", "priority": 5, "template": "bruise"},
    {"name": "Contact Lens Issue", "priority": 5, "template": "contact_lens"},
]

SENIOR_EXPRESSIVE = """Patient: {age}-year-old {gender}
Chief Complaint: {cc}

History of Present Illness:
{hpi}

Vital Signs:
- BP: {bp}
- HR: {hr}
- RR: {rr}
- SpO2: {spo2}
- Temp: {temp}

Physical Examination:
{pe}

{additional}

Past Medical History: {pmh}
Medications: {meds}
Allergies: {allergies}
"""

SENIOR_CONCISE = """Patient: {age}yo {gender}
CC: {cc}
HPI: {hpi}
VS: BP {bp}, HR {hr}, RR {rr}, SpO2 {spo2}, T {temp}
PE: {pe}
{additional}
PMH: {pmh}
Meds: {meds}
Allergies: {allergies}
"""

R1_EXPRESSIVE = """Patient: {age}-year-old {gender}
Chief Complaint: {cc}

History of Present Illness:
{hpi}

Vital Signs:
- BP: {bp} mmHg
- HR: {hr} bpm
- RR: {rr} breaths/min
- SpO2: {spo2}% on room air
- Temp: {temp}°C

Physical Examination:
{pe}

{additional}

Past Medical History: {pmh}
Medications: {meds}
Allergies: {allergies}
Social History: {social}
"""

R1_CONCISE = """Pt: {age}yo {gender}
CC: {cc}
HPI: {hpi}
VS: {bp}/{hr}/{rr}/{spo2}/{temp}
PE: {pe}
{additional}
PMH: {pmh}
Meds: {meds}
Allergies: {allergies}
"""

SENIOR_NARRATIVE = """{age}yo {gender} with {cc}. {hpi} Vitals: BP {bp}, HR {hr}, RR {rr}, SpO2 {spo2}%, T {temp}C. Exam: {pe} {additional} PMH: {pmh}. Meds: {meds}. Allergies: {allergies}."""

R1_NARRATIVE = """{age}yo {gender} presenting with {cc}. {hpi} Vitals stable/unstable: BP {bp}, HR {hr}, RR {rr}, SpO2 {spo2}%, T {temp}C. On exam: {pe} {additional} PMH significant for {pmh}. Currently on {meds}. Allergies: {allergies}. Social: {social}"""

SENIOR_STREAM = """{cc} in a {age}yo {gender}. {hpi} VS: {bp}/{hr}/{rr}/{spo2}/{temp}. {pe} {additional} PMH: {pmh} Meds: {meds} Allergies: {allergies}"""

R1_STREAM = """{age}yo {gender}, {cc}. {hpi} Vitals: {bp}, {hr}, {rr}, {spo2}%, {temp}C. {pe} {additional} PMH: {pmh}. Meds: {meds}. Allergies: {allergies}. Social: {social}"""

SENIOR_BULLETS = """- Patient: {age}yo {gender}
- CC: {cc}
- HPI: {hpi}
- VS: BP {bp} | HR {hr} | RR {rr} | SpO2 {spo2} | Temp {temp}
- PE: {pe}
- Workup: {additional}
- PMH: {pmh}
- Meds: {meds}
- Allergies: {allergies}"""

R1_BULLETS = """* {age}yo {gender}
* CC: {cc}
* HPI: {hpi}
* VS: {bp} / {hr} / {rr} / {spo2} / {temp}
* PE: {pe}
* Workup: {additional}
* PMH: {pmh}
* Meds: {meds}
* Allergies: {allergies}
* Social: {social}"""

SENIOR_SOAP = """S: {age}yo {gender} with {cc}. {hpi}
O: Vitals: BP {bp}, HR {hr}, RR {rr}, SpO2 {spo2}%, T {temp}C. PE: {pe} {additional}
A: {pmh}
P: Continue current management. Meds: {meds}. Allergies: {allergies}"""

R1_SOAP = """S: {age}yo {gender} presents with {cc}. {hpi}
O: Vitals: {bp}, {hr}, {rr}, {spo2}%, {temp}C. Exam: {pe} {additional}
A: PMH: {pmh}
P: Plan: Meds: {meds}. Allergies: {allergies}. Social: {social}"""


def generate_vitals(priority):
    if priority == 1:
        return {
            "bp": f"{random.randint(70, 90)}/{random.randint(40, 60)}",
            "hr": random.randint(120, 160),
            "rr": random.randint(28, 40),
            "spo2": random.randint(82, 90),
            "temp": round(random.uniform(38.5, 40.5), 1),
        }
    elif priority == 2:
        return {
            "bp": f"{random.randint(90, 110)}/{random.randint(60, 75)}",
            "hr": random.randint(100, 130),
            "rr": random.randint(22, 30),
            "spo2": random.randint(90, 94),
            "temp": round(random.uniform(37.8, 39.2), 1),
        }
    elif priority == 3:
        return {
            "bp": f"{random.randint(110, 140)}/{random.randint(70, 90)}",
            "hr": random.randint(85, 110),
            "rr": random.randint(18, 24),
            "spo2": random.randint(94, 97),
            "temp": round(random.uniform(37.2, 38.5), 1),
        }
    elif priority == 4:
        return {
            "bp": f"{random.randint(110, 135)}/{random.randint(65, 85)}",
            "hr": random.randint(70, 95),
            "rr": random.randint(14, 20),
            "spo2": random.randint(96, 99),
            "temp": round(random.uniform(36.5, 37.5), 1),
        }
    else:
        return {
            "bp": f"{random.randint(105, 130)}/{random.randint(60, 80)}",
            "hr": random.randint(60, 85),
            "rr": random.randint(12, 18),
            "spo2": random.randint(97, 100),
            "temp": round(random.uniform(36.3, 37.2), 1),
        }


def generate_case(index):
    condition = CONDITIONS[index % len(CONDITIONS)]
    priority = condition["priority"]

    profiles = [
        "senior_expressive", "senior_concise", "r1_expressive", "r1_concise",
        "senior_narrative", "r1_narrative", "senior_stream", "r1_stream",
        "senior_bullets", "r1_bullets", "senior_soap", "r1_soap",
    ]
    profile = profiles[index % 12]

    age = random.randint(18, 90)
    gender = random.choice(["male", "female"])
    vitals = generate_vitals(priority)

    templates = {
        "chest_pain_stemi": {
            "cc": "Chest pain for 1 hour",
            "hpi": "The patient presents with sudden onset substernal chest pain that began 1 hour ago. The pain is described as pressure-like, 9/10 in severity, radiating to the left arm and jaw. Associated symptoms include diaphoresis, nausea, and dyspnea.",
            "pe": "- General: Diaphoretic, appears distressed\n- Cardiovascular: Tachycardic, regular rhythm\n- Respiratory: Mild bilateral crackles",
            "additional": "ECG: ST-segment elevation in leads V1-V4\nTroponin: Elevated\nCXR: Mild pulmonary congestion",
            "pmh": "Hypertension, hyperlipidemia, smoking history",
            "meds": "Aspirin, atorvastatin, lisinopril",
            "allergies": "No known drug allergies",
            "social": "Smoker (20 pack-years), occasional alcohol",
        },
        "cardiac_arrest": {
            "cc": "Unresponsive, found down",
            "hpi": "Witnessed collapse 15 minutes ago. Bystander CPR initiated immediately. EMS arrived and found patient in ventricular fibrillation. Two shocks delivered with ROSC achieved.",
            "pe": "- General: Unresponsive, intubated\n- Cardiovascular: Weak pulses, tachycardic\n- Respiratory: Mechanical ventilation\n- Neurological: Pupils reactive, no response to pain",
            "additional": "ECG: Ventricular fibrillation converted to sinus rhythm\nABG: pH 7.18, pCO2 55, lactate 8.2\nGlucose: 180 mg/dL",
            "pmh": "Coronary artery disease, previous MI",
            "meds": "Metoprolol, clopidogrel, atorvastatin",
            "allergies": "Penicillin",
            "social": "Former smoker, sedentary lifestyle",
        },
        "severe_sepsis": {
            "cc": "Fever and confusion for 2 days",
            "hpi": "The patient presents with 2 days of fever, chills, and progressive confusion. Found at home by family member. Last seen normal 48 hours ago. Possible urinary source.",
            "pe": "- General: Ill-appearing, confused\n- Cardiovascular: Tachycardic, hypotensive\n- Respiratory: Tachypneic, clear lungs\n- Skin: Warm, flushed, petechiae on trunk",
            "additional": "WBC: 22,000\nLactate: 5.8\nCreatinine: 2.4\nUrinalysis: Positive leukocytes, nitrites\nBlood cultures: Pending",
            "pmh": "Diabetes mellitus, recurrent UTIs",
            "meds": "Metformin, insulin",
            "allergies": "Sulfa drugs",
            "social": "Lives alone, limited mobility",
        },
        "ich": {
            "cc": "Sudden severe headache and vomiting",
            "hpi": "The patient presents with sudden onset 'worst headache of life' 2 hours ago while at rest. Associated with vomiting and progressive drowsiness. No history of trauma.",
            "pe": "- General: Drowsy but arousable\n- Cardiovascular: Hypertensive\n- Neurological: Left-sided weakness, neck stiffness, photophobia",
            "additional": "CT Head: Large right-sided intracerebral hemorrhage with midline shift\nINR: 1.0\nPlatelets: 220,000",
            "pmh": "Hypertension (non-compliant)",
            "meds": "None (non-compliant with antihypertensives)",
            "allergies": "No known drug allergies",
            "social": "Smoker, poor medication adherence",
        },
        "tension_pneumo": {
            "cc": "Sudden chest pain and severe dyspnea",
            "hpi": "The patient presents with sudden onset right-sided chest pain and severe shortness of breath 1 hour ago while climbing stairs. Pain is sharp, pleuritic. Rapidly worsening dyspnea.",
            "pe": "- General: Severe respiratory distress\n- Cardiovascular: Tachycardic, hypotensive\n- Respiratory: Absent breath sounds right side, hyperresonance to percussion\n- Trachea: Deviated to left",
            "additional": "CXR: Right tension pneumothorax with mediastinal shift\nABG: pH 7.28, pCO2 50, pO2 60",
            "pmh": "COPD, emphysema",
            "meds": "Albuterol, tiotropium",
            "allergies": "No known drug allergies",
            "social": "Heavy smoker (40 pack-years)",
        },
        "anaphylaxis": {
            "cc": "Difficulty breathing and throat tightness after eating",
            "hpi": "The patient developed facial swelling, urticaria, and difficulty breathing 30 minutes after eating shellfish. Symptoms rapidly progressing. Used EpiPen with minimal relief.",
            "pe": "- General: Anxious, diaphoretic\n- Cardiovascular: Tachycardic, hypotensive\n- Respiratory: Stridor, wheezing, periorbital edema\n- Skin: Generalized urticaria, angioedema",
            "additional": "Tryptase: Elevated\nNo labs drawn yet - clinical diagnosis",
            "pmh": "Shellfish allergy (previous mild reactions)",
            "meds": "None",
            "allergies": "Shellfish (known)",
            "social": "No tobacco or alcohol use",
        },
        "dka_severe": {
            "cc": "Nausea, vomiting, and confusion",
            "hpi": "The patient presents with 3 days of polyuria, polydipsia, nausea, and vomiting. Today found confused by family. Known diabetes, stopped insulin 2 days ago due to poor oral intake.",
            "pe": "- General: Dehydrated, Kussmaul breathing\n- Cardiovascular: Tachycardic, hypotensive\n- Neurological: Confused, disoriented",
            "additional": "Glucose: 680 mg/dL\npH: 7.08\nBicarbonate: 8\nAnion gap: 28\nKetones: Large\nPotassium: 5.8",
            "pmh": "Type 1 diabetes mellitus",
            "meds": "Insulin (recently stopped)",
            "allergies": "No known drug allergies",
            "social": "Young adult, irregular follow-up",
        },
        "massive_pe": {
            "cc": "Sudden dyspnea and pleuritic chest pain",
            "hpi": "The patient presents with sudden onset severe dyspnea and right-sided pleuritic chest pain 2 hours ago. Recent long-haul flight 3 days prior. Syncope on presentation.",
            "pe": "- General: Severe distress, diaphoretic\n- Cardiovascular: Tachycardic, hypotensive, JVD\n- Respiratory: Tachypneic, decreased breath sounds right base",
            "additional": "CT PE: Massive pulmonary embolism with right heart strain\nTroponin: Elevated\nBNP: Elevated\nD-dimer: >5000",
            "pmh": "Obesity, oral contraceptive use",
            "meds": "Oral contraceptives",
            "allergies": "No known drug allergies",
            "social": "Recent long-distance travel",
        },
        "status_epilepticus": {
            "cc": "Continuous seizure activity",
            "hpi": "The patient witnessed to have continuous tonic-clonic seizure activity for 25 minutes. Multiple seizures without regaining consciousness between episodes. EMS administered lorazepam 2mg IV with partial response.",
            "pe": "- General: Post-ictal, minimally responsive\n- Cardiovascular: Tachycardic\n- Respiratory: Gurgling, requires airway support\n- Neurological: No purposeful movement",
            "additional": "Glucose: 110 mg/dL\nLactate: 4.2\nCT Head: Pending\nEEG: Pending",
            "pmh": "Epilepsy (poorly controlled)",
            "meds": "Levetiracetam (non-compliant)",
            "allergies": "No known drug allergies",
            "social": "History of medication non-compliance",
        },
        "aortic_dissection": {
            "cc": "Tearing chest pain radiating to back",
            "hpi": "The patient presents with sudden onset severe 'tearing' chest pain radiating to the back 2 hours ago. Pain is maximal at onset. History of uncontrolled hypertension.",
            "pe": "- General: Diaphoretic, appears in severe pain\n- Cardiovascular: BP differential between arms (180/100 right, 140/85 left)\n- Respiratory: Clear lungs\n- Neurological: Intact",
            "additional": "CT Angio: Type A aortic dissection involving ascending aorta\nECG: Sinus tachycardia, no STEMI",
            "pmh": "Hypertension (poorly controlled), Marfanoid habitus",
            "meds": "Amlodipine (non-compliant)",
            "allergies": "No known drug allergies",
            "social": "Smoker, poor healthcare follow-up",
        },
        "nstemi": {
            "cc": "Chest pain for 4 hours",
            "hpi": "The patient presents with 4 hours of intermittent substernal chest pressure, 6/10, with exertion. Relieved partially with rest. No radiation. Mild diaphoresis.",
            "pe": "- General: Mild distress\n- Cardiovascular: Regular rhythm, no murmurs\n- Respiratory: Clear lungs",
            "additional": "ECG: T-wave inversions in V4-V6\nTroponin: 0.8 (elevated)\nCXR: Normal",
            "pmh": "Hypertension, diabetes",
            "meds": "Metformin, lisinopril, aspirin",
            "allergies": "No known drug allergies",
            "social": "Smoker (10 pack-years)",
        },
        "stroke": {
            "cc": "Sudden left-sided weakness",
            "hpi": "The patient witnessed to have sudden onset left-sided weakness and facial droop 3 hours ago while eating breakfast. Last seen normal 3.5 hours ago. No trauma.",
            "pe": "- General: Alert, oriented\n- Cardiovascular: Atrial fibrillation on monitor\n- Neurological: Left facial droop, left arm/leg weakness (NIHSS 12), dysarthria",
            "additional": "CT Head: No hemorrhage\nCT Angio: Right MCA occlusion\nGlucose: 145 mg/dL",
            "pmh": "Atrial fibrillation (not anticoagulated), hypertension",
            "meds": "Metoprolol, amlodipine",
            "allergies": "No known drug allergies",
            "social": "Lives with spouse",
        },
        "pneumonia_severe": {
            "cc": "Fever, cough, and difficulty breathing",
            "hpi": "The patient presents with 4 days of fever, productive cough, and worsening shortness of breath. Now unable to walk without severe dyspnea. Decreased oral intake.",
            "pe": "- General: Ill-appearing, dehydrated\n- Cardiovascular: Tachycardic\n- Respiratory: Crackles right lower lobe, dull to percussion\n- SpO2: 88% on room air",
            "additional": "CXR: Right lower lobe consolidation with effusion\nWBC: 18,000\nLactate: 2.8\nBlood cultures: Pending",
            "pmh": "COPD, diabetes",
            "meds": "Albuterol, metformin",
            "allergies": "Penicillin (rash)",
            "social": "Smoker (30 pack-years)",
        },
        "gi_bleed": {
            "cc": "Vomiting blood and black stools",
            "hpi": "The patient presents with 2 episodes of hematemesis and melena for 2 days. Feels dizzy on standing. History of NSAID use for chronic back pain.",
            "pe": "- General: Pale, diaphoretic\n- Cardiovascular: Tachycardic, orthostatic hypotension\n- Abdomen: Soft, non-tender, no masses",
            "additional": "Hemoglobin: 7.2 (baseline 13)\nINR: 1.0\nBUN/Cr ratio: 35\nType and crossmatch: Done",
            "pmh": "Chronic back pain, osteoarthritis",
            "meds": "Ibuprofen 800mg TID, acetaminophen",
            "allergies": "No known drug allergies",
            "social": "No alcohol use",
        },
        "pyelo": {
            "cc": "Fever and flank pain",
            "hpi": "The patient presents with 3 days of fever, chills, right flank pain, and dysuria. Nausea with vomiting. Unable to tolerate oral intake.",
            "pe": "- General: Appears uncomfortable\n- Cardiovascular: Tachycardic\n- Abdomen: Right CVA tenderness\n- Genitourinary: No discharge",
            "additional": "WBC: 16,000\nUrinalysis: Positive leukocytes, nitrites, blood\nUrine culture: Pending\nCT KUB: Right hydronephrosis, 6mm stone",
            "pmh": "Recurrent UTIs, kidney stones",
            "meds": "None",
            "allergies": "No known drug allergies",
            "social": "Sexually active, uses condoms",
        },
        "copd_exac": {
            "cc": "Worsening shortness of breath",
            "hpi": "The patient presents with 3 days of worsening dyspnea, increased sputum production, and wheezing. Using rescue inhaler every 2 hours with minimal relief. Unable to sleep due to breathlessness.",
            "pe": "- General: Respiratory distress, using accessory muscles\n- Cardiovascular: Tachycardic\n- Respiratory: Bilateral wheezing, prolonged expiratory phase",
            "additional": "ABG: pH 7.32, pCO2 58, pO2 65\nCXR: Hyperinflation, no pneumonia\nPeak flow: 40% of personal best",
            "pmh": "COPD (GOLD III), home oxygen",
            "meds": "Albuterol, tiotropium, prednisone",
            "allergies": "No known drug allergies",
            "social": "Smoker (50 pack-years), on home O2",
        },
        "chf_acute": {
            "cc": "Shortness of breath and leg swelling",
            "hpi": "The patient presents with 5 days of progressive dyspnea, orthopnea, and bilateral leg swelling. Gained 5kg in 1 week. Unable to lie flat. History of heart failure.",
            "pe": "- General: Distressed, orthopneic\n- Cardiovascular: Tachycardic, JVD, S3 gallop\n- Respiratory: Bilateral crackles to mid-lung fields\n- Extremities: Bilateral pitting edema to knees",
            "additional": "BNP: 2500\nCXR: Pulmonary edema, cardiomegaly\nEcho (prior): EF 25%",
            "pmh": "Heart failure (EF 25%), hypertension, diabetes",
            "meds": "Furosemide, carvedilol, lisinopril, metformin",
            "allergies": "No known drug allergies",
            "social": "High salt diet, poor fluid restriction",
        },
        "meningitis": {
            "cc": "Fever, headache, and neck stiffness",
            "hpi": "The patient presents with 2 days of severe headache, fever, and progressive neck stiffness. Photophobia and vomiting. Roommate similar symptoms 1 week ago.",
            "pe": "- General: Ill-appearing, photophobic\n- Cardiovascular: Tachycardic\n- Neurological: Neck stiffness, positive Kernig's sign, no focal deficits",
            "additional": "WBC: 18,000\nCT Head: No contraindication to LP\nLP: Opening pressure 28, WBC 800 (90% PMNs), protein 120, glucose 30",
            "pmh": "None",
            "meds": "None",
            "allergies": "No known drug allergies",
            "social": "College student, lives in dormitory",
        },
        "appendicitis": {
            "cc": "Right lower quadrant abdominal pain",
            "hpi": "The patient presents with 18 hours of periumbilical pain that migrated to the right lower quadrant. Associated with nausea, vomiting, and anorexia. Low-grade fever.",
            "pe": "- General: Appears uncomfortable, lying still\n- Cardiovascular: Tachycardic\n- Abdomen: RLQ tenderness, guarding, positive Rovsing's sign",
            "additional": "WBC: 14,000\nCT Abdomen: Appendicolith, dilated appendix (12mm), fat stranding",
            "pmh": "None",
            "meds": "None",
            "allergies": "No known drug allergies",
            "social": "No significant history",
        },
        "ectopic": {
            "cc": "Lower abdominal pain and vaginal bleeding",
            "hpi": "The patient presents with 6 weeks of amenorrhea, sudden onset right lower quadrant pain, and vaginal spotting. Positive home pregnancy test. Pain is severe and worsening.",
            "pe": "- General: Pale, appears in pain\n- Cardiovascular: Tachycardic, borderline hypotensive\n- Abdomen: Right adnexal tenderness, cervical motion tenderness",
            "additional": "Beta-hCG: 2500\nTransvaginal US: No intrauterine pregnancy, right adnexal mass with free fluid",
            "pmh": "Pelvic inflammatory disease (prior)",
            "meds": "None",
            "allergies": "No known drug allergies",
            "social": "Sexually active, no contraception",
        },
        "renal_colic": {
            "cc": "Severe flank pain radiating to groin",
            "hpi": "The patient presents with sudden onset severe left flank pain radiating to the groin, 8/10, colicky in nature. Nausea and vomiting. Unable to find comfortable position.",
            "pe": "- General: Restless, appears in severe pain\n- Cardiovascular: Normal\n- Abdomen: Soft, left CVA tenderness\n- Genitourinary: No discharge",
            "additional": "Urinalysis: Microscopic hematuria\nCT KUB: 5mm left ureteral stone, mild hydronephrosis",
            "pmh": "Kidney stones (prior episode 2 years ago)",
            "meds": "None.",
            "allergies": "No known drug allergies",
            "social": "Low fluid intake, high salt diet",
        },
        "migraine": {
            "cc": "Severe headache with visual aura",
            "hpi": "The patient presents with 6 hours of severe right-sided throbbing headache preceded by visual aura (scintillating scotoma). Photophobia and phonophobia. Nausea. History of similar headaches.",
            "pe": "- General: Appears uncomfortable, prefers dark room\n- Cardiovascular: Normal\n- Neurological: No focal deficits, fundi normal",
            "additional": "CT Head: Normal (performed due to first severe episode)\nNo labs indicated",
            "pmh": "Migraine with aura (since adolescence)",
            "meds": "Sumatriptan (OTC)",
            "allergies": "No known drug allergies",
            "social": "High stress job, poor sleep",
        },
        "asthma_mod": {
            "cc": "Wheezing and shortness of breath",
            "hpi": "The patient presents with 2 days of worsening wheezing, chest tightness, and shortness of breath. Using albuterol inhaler every 3 hours with partial relief. Upper respiratory infection 1 week ago.",
            "pe": "- General: Mild respiratory distress\n- Cardiovascular: Tachycardic\n- Respiratory: Bilateral wheezing, prolonged expiratory phase",
            "additional": "Peak flow: 60% of personal best\nABG: pH 7.38, pCO2 42, pO2 78\nCXR: Hyperinflation, no infiltrate",
            "pmh": "Asthma (moderate persistent)",
            "meds": "Albuterol, fluticasone",
            "allergies": "Dust mites, pollen",
            "social": "Smoker (5 pack-years)",
        },
        "uti": {
            "cc": "Dysuria and urinary frequency",
            "hpi": "The patient presents with 3 days of dysuria, urinary frequency, and urgency. Suprapubic discomfort. No fever or flank pain. Sexually active.",
            "pe": "- General: Well-appearing\n- Cardiovascular: Normal\n- Abdomen: Suprapubic tenderness\n- Genitourinary: No discharge",
            "additional": "Urinalysis: Positive leukocytes, nitrites, bacteria\nUrine culture: Pending",
            "pmh": "Recurrent UTIs (3 in past year)",
            "meds": "None.",
            "allergies": "No known drug allergies",
            "social": "Sexually active, new partner 1 month ago",
        },
        "cellulitis": {
            "cc": "Redness and swelling on left leg",
            "hpi": "The patient presents with 3 days of progressive redness, swelling, and warmth on the left lower leg. Minor abrasion 5 days ago. Low-grade fever. No improvement with elevation.",
            "pe": "- General: Mild fever\n- Cardiovascular: Normal\n- Extremities: Erythema, warmth, tenderness left calf, no crepitus, no fluctuance",
            "additional": "WBC: 12,000\nNo abscess on exam\nBlood cultures: Not indicated",
            "pmh": "Diabetes mellitus, peripheral neuropathy",
            "meds": "Metformin, gabapentin",
            "allergies": "No known drug allergies",
            "social": "Poor foot care, walks barefoot at home",
        },
        "dvt": {
            "cc": "Left leg swelling and pain",
            "hpi": "The patient presents with 4 days of progressive left calf swelling, pain, and warmth. Recent surgery (knee arthroscopy) 2 weeks ago. Immobilized for 1 week post-op.",
            "pe": "- General: Well-appearing\n- Cardiovascular: Normal\n- Extremities: Left calf swelling (3cm difference), tenderness, Homans sign positive",
            "additional": "D-dimer: 1200\nUS Doppler: Left popliteal vein thrombosis",
            "pmh": "Obesity, recent knee surgery",
            "meds": "Ibuprofen, acetaminophen",
            "allergies": "No known drug allergies",
            "social": "Post-operative, limited mobility",
        },
        "afib": {
            "cc": "Palpitations and dizziness",
            "hpi": "The patient presents with 6 hours of palpitations, irregular heartbeat, and lightheadedness. No chest pain or syncope. History of intermittent palpitations.",
            "pe": "- General: Mild distress\n- Cardiovascular: Irregularly irregular rhythm, rate 140\n- Respiratory: Clear lungs",
            "additional": "ECG: Atrial fibrillation with rapid ventricular response\nTroponin: 0.01 (normal)\nTSH: Normal\nElectrolytes: Normal",
            "pmh": "Hypertension, hyperthyroidism (treated)",
            "meds": "Lisinopril, methimazole",
            "allergies": "No known drug allergies",
            "social": "High caffeine intake, poor sleep",
        },
        "diverticulitis": {
            "cc": "Left lower quadrant pain and fever",
            "hpi": "The patient presents with 3 days of left lower quadrant pain, low-grade fever, and constipation. Pain is constant and worsening. Decreased appetite.",
            "pe": "- General: Mild fever\n- Cardiovascular: Tachycardic\n- Abdomen: LLQ tenderness, no rebound or guarding",
            "additional": "WBC: 13,000\nCT Abdomen: Sigmoid diverticulitis with fat stranding, no abscess",
            "pmh": "Diverticulosis (known), constipation",
            "meds": "Psyllium, docusate",
            "allergies": "No known drug allergies",
            "social": "Low fiber diet, sedentary",
        },
        "cholecystitis": {
            "cc": "Right upper quadrant pain after fatty meal",
            "hpi": "The patient presents with 12 hours of severe right upper quadrant pain after a fatty meal, radiating to the right scapula. Nausea and vomiting. Low-grade fever.",
            "pe": "- General: Appears uncomfortable\n- Cardiovascular: Tachycardic\n- Abdomen: RUQ tenderness, positive Murphy's sign",
            "additional": "WBC: 14,000\nUS Gallbladder: Gallstones, wall thickening, pericholecystic fluid\nLFTs: Normal",
            "pmh": "Gallstones (known), obesity",
            "meds": "None",
            "allergies": "No known drug allergies",
            "social": "High fat diet, rapid weight loss",
        },
        "pancreatitis": {
            "cc": "Severe epigastric pain radiating to back",
            "hpi": "The patient presents with 12 hours of severe epigastric pain radiating to the back, worse when lying flat. Nausea and vomiting. History of alcohol use.",
            "pe": "- General: Appears in severe pain\n- Cardiovascular: Tachycardic\n- Abdomen: Epigastric tenderness, no guarding",
            "additional": "Lipase: 1200\nCT Abdomen: Pancreatic edema, no necrosis\nTriglycerides: 450",
            "pmh": "Alcohol use disorder, hypertriglyceridemia",
            "meds": "None.",
            "allergies": "No known drug allergies",
            "social": "Alcohol: 6-8 drinks daily for 10 years",
        },
        "sprain": {
            "cc": "Right ankle pain after twisting injury",
            "hpi": "The patient presents with right ankle pain after twisting injury while playing basketball 2 hours ago. Able to bear weight with difficulty. Swelling and bruising developing.",
            "pe": "- General: Mild distress\n- Extremities: Right ankle swelling, tenderness over lateral malleolus, no bony tenderness, full range of motion with pain",
            "additional": "X-ray Right Ankle: No fracture (Ottawa rules negative)\nNo ligamentous instability",
            "pmh": "None",
            "meds": "None",
            "allergies": "No known drug allergies",
            "social": "Recreational basketball player",
        },
        "laceration": {
            "cc": "Laceration on left hand",
            "hpi": "The patient presents with a laceration on the left hand sustained 1 hour ago while cutting vegetables. Bleeding controlled with direct pressure. No loss of sensation or motor function.",
            "pe": "- General: Well-appearing\n- Left Hand: 2 cm laceration on palmar surface, no active bleeding, full ROM, sensation intact",
            "additional": "Tetanus: Up to date\nNo imaging needed",
            "pmh": "None",
            "meds": "None",
            "allergies": "No known drug allergies",
            "social": "No significant history",
        },
        "otitis": {
            "cc": "Right ear pain and fever",
            "hpi": "The patient presents with 2 days of right ear pain, fever, and decreased hearing. Pulling at ear. Upper respiratory infection 1 week ago. No discharge.",
            "pe": "- General: Mild fever, irritable\n- ENT: Right tympanic membrane erythematous, bulging, decreased mobility\n- No mastoid tenderness",
            "additional": "No labs indicated\nDiagnosis: Acute otitis media",
            "pmh": "Recurrent ear infections (childhood)",
            "meds": "None",
            "allergies": "Amoxicillin (rash)",
            "social": "Daycare attendance",
        },
        "pharyngitis": {
            "cc": "Sore throat and difficulty swallowing",
            "hpi": "The patient presents with 3 days of sore throat, difficulty swallowing, and fever. No cough or rhinorrhea. Tender anterior cervical lymphadenopathy.",
            "pe": "- General: Mild fever\n- ENT: Erythematous pharynx, tonsillar exudates, no trismus\n- Neck: Tender anterior cervical lymphadenopathy",
            "additional": "Rapid strep: Positive\nCentor score: 4",
            "pmh": "None",
            "meds": "None",
            "allergies": "No known drug allergies",
            "social": "Works in office, close contact with sick coworker",
        },
        "conjunctivitis": {
            "cc": "Redness and discharge in right eye",
            "hpi": "The patient presents with 2 days of right eye redness, itching, and purulent discharge. Worse in morning with eyelids stuck together. No vision changes. Left eye now affected.",
            "pe": "- General: Well-appearing\n- Eyes: Bilateral conjunctival injection, purulent discharge, no corneal involvement, visual acuity normal",
            "additional": "No labs indicated\nDiagnosis: Bacterial conjunctivitis",
            "pmh": "None",
            "meds": "None",
            "allergies": "No known drug allergies",
            "social": "Contact lens wearer, poor hygiene",
        },
        "allergy_minor": {
            "cc": "Hives and itching after medication",
            "hpi": "The patient presents with generalized urticaria and pruritus 1 hour after taking amoxicillin for sore throat. No respiratory distress, no facial swelling. No prior antibiotic exposure.",
            "pe": "- General: Well-appearing, mild distress\n- Skin: Generalized urticaria, no angioedema\n- Respiratory: Clear lungs, no wheezing",
            "additional": "No labs indicated\nDiagnosis: Acute urticaria, likely drug reaction",
            "pmh": "None.",
            "meds": "Amoxicillin (started today)",
            "allergies": "Amoxicillin (new reaction)",
            "social": "No significant history",
        },
        "dermatitis": {
            "cc": "Itchy rash on both hands",
            "hpi": "The patient presents with 1 week of pruritic rash on both hands. Works as a hairdresser. Worse after work. No fever or systemic symptoms. Previous episodes.",
            "pe": "- General: Well-appearing\n- Skin: Erythematous, scaly, lichenified plaques on dorsal hands, no vesicles or oozing",
            "additional": "No labs indicated\nDiagnosis: Contact dermatitis (irritant)",
            "pmh": "Atopic dermatitis (childhood)",
            "meds": "Hydrocortisone cream (OTC)",
            "allergies": "No known drug allergies",
            "social": "Hairdresser, frequent hand washing",
        },
        "head_injury_minor": {
            "cc": "Head injury after fall",
            "hpi": "The patient presents after falling off a bicycle 2 hours ago, hitting head on pavement. No loss of consciousness. Mild headache and nausea. No vomiting. Wearing helmet.",
            "pe": "- General: Alert, oriented\n- HEENT: Small abrasion on right temporal area, no hematoma\n- Neurological: No focal deficits, GCS 15",
            "additional": "CT Head: Not indicated (Canadian CT Head Rule negative)\nGCS: 15",
            "pmh": "None.",
            "meds": "None",
            "allergies": "No known drug allergies",
            "social": "Cyclist, helmet use",
        },
        "strain": {
            "cc": "Lower back pain after lifting",
            "hpi": "The patient presents with acute lower back pain after lifting heavy boxes 1 day ago. Pain is mechanical, worse with bending and lifting. No radiation to legs. No bowel/bladder changes.",
            "pe": "- General: Mild distress\n- Musculoskeletal: Paraspinal muscle tenderness, no midline tenderness, straight leg raise negative bilaterally",
            "additional": "No imaging indicated\nDiagnosis: Lumbar muscle strain",
            "pmh": "None.",
            "meds": "Ibuprofen (OTC)",
            "allergies": "No known drug allergies",
            "social": "Sedentary job, poor lifting technique",
        },
        "insect_bite": {
            "cc": "Painful swelling on left arm after insect bite",
            "hpi": "The patient presents with painful swelling and redness on left forearm after insect bite 1 day ago. Mild itching. No fever or systemic symptoms. No difficulty breathing.",
            "pe": "- General: Well-appearing\n- Skin: 3cm area of erythema and swelling on left forearm, central punctum, no fluctuance",
            "additional": "No labs indicated\nDiagnosis: Insect bite, local reaction",
            "pmh": "None.",
            "meds": "None.",
            "allergies": "No known drug allergies",
            "social": "Camping trip 2 days ago",
        },
        "cold": {
            "cc": "Runny nose, cough, and sore throat",
            "hpi": "The patient presents with 3 days of rhinorrhea, nasal congestion, cough, and sore throat. Low-grade fever. No difficulty breathing. Symptoms improving.",
            "pe": "- General: Well-appearing\n- HEENT: Erythematous pharynx, clear rhinorrhea, no tonsillar exudates\n- Respiratory: Clear lungs",
            "additional": "No labs indicated\nDiagnosis: Viral upper respiratory infection",
            "pmh": "None.",
            "meds": "Acetaminophen (OTC)",
            "allergies": "No known drug allergies",
            "social": "Works in office, sick contacts",
        },
        "headache_mild": {
            "cc": "Mild headache for 2 days",
            "hpi": "The patient presents with 2 days of mild bilateral frontal headache, 3/10, worse with stress. No nausea, vomiting, or visual changes. Relieved with rest and OTC analgesics.",
            "pe": "- General: Well-appearing\n- Neurological: No focal deficits, fundi normal, no neck stiffness",
            "additional": "No labs or imaging indicated\nDiagnosis: Tension-type headache",
            "pmh": "Tension headaches (occasional)",
            "meds": "Acetaminophen (OTC)",
            "allergies": "No known drug allergies",
            "social": "High stress job, poor sleep hygiene",
        },
        "refill": {
            "cc": "Request for medication refill",
            "hpi": "The patient presents for refill of lisinopril 10mg for hypertension. No complaints. BP well-controlled. Last seen 6 months ago. Ran out of medication 1 week ago.",
            "pe": "- General: Well-appearing\n- Cardiovascular: Regular rhythm, no murmurs\n- BP: 128/82",
            "additional": "No labs indicated\nStable chronic condition",
            "pmh": "Hypertension (well-controlled)",
            "meds": "Lisinopril 10mg (refill requested)",
            "allergies": "No known drug allergies",
            "social": "Lives alone, independent",
        },
        "rash_mild": {
            "cc": "Mild itchy rash on trunk",
            "hpi": "The patient presents with 3 days of mild pruritic rash on trunk and upper extremities. No fever. Started after new laundry detergent. No mucosal involvement.",
            "pe": "- General: Well-appearing\n- Skin: Erythematous maculopapular rash on trunk and upper extremities, no vesicles or desquamation",
            "additional": "No labs indicated\nDiagnosis: Allergic contact dermatitis",
            "pmh": "None.",
            "meds": "None.",
            "allergies": "No known drug allergies",
            "social": "New laundry detergent 1 week ago",
        },
        "sore_throat": {
            "cc": "Sore throat for 2 days",
            "hpi": "The patient presents with 2 days of sore throat, worse with swallowing. No fever, cough, or rhinorrhea. No difficulty breathing or drooling.",
            "pe": "- General: Well-appearing\n- ENT: Mild pharyngeal erythema, no exudates, no tonsillar enlargement\n- Neck: No lymphadenopathy",
            "additional": "Rapid strep: Negative\nCentor score: 1",
            "pmh": "None.",
            "meds": "None.",
            "allergies": "No known drug allergies",
            "social": "No significant history",
        },
        "back_pain_mild": {
            "cc": "Lower back pain for 1 week",
            "hpi": "The patient presents with 1 week of mild lower back pain, worse with prolonged sitting. No radiation to legs. No bowel or bladder changes. No trauma. Improving with rest.",
            "pe": "- General: Well-appearing\n- Musculoskeletal: Mild paraspinal tenderness, no midline tenderness, straight leg raise negative",
            "additional": "No imaging indicated\nDiagnosis: Mechanical low back pain",
            "pmh": "None.",
            "meds": "Ibuprofen (OTC)",
            "allergies": "No known drug allergies",
            "social": "Desk job, sedentary lifestyle",
        },
        "anxiety": {
            "cc": "Chest tightness and palpitations",
            "hpi": "The patient presents with 1 hour of chest tightness, palpitations, and feeling of impending doom. Hyperventilating. Similar episodes in the past, triggered by stress. No radiation or diaphoresis.",
            "pe": "- General: Anxious, hyperventilating\n- Cardiovascular: Tachycardic, regular rhythm\n- Respiratory: Clear lungs\n- Neurological: No focal deficits",
            "additional": "ECG: Sinus tachycardia, no ischemic changes\nTroponin: Negative\nABG: Respiratory alkalosis",
            "pmh": "Anxiety disorder, panic attacks",
            "meds": "Sertraline",
            "allergies": "No known drug allergies",
            "social": "High stress job, recent life changes",
        },
        "insomnia": {
            "cc": "Difficulty sleeping for 2 weeks",
            "hpi": "The patient presents with 2 weeks of difficulty falling and staying asleep. Fatigue during day. No snoring or witnessed apneas. Stress at work. Drinks coffee in afternoon.",
            "pe": "- General: Well-appearing, tired\n- Neurological: No focal deficits",
            "additional": "No labs indicated\nDiagnosis: Acute insomnia",
            "pmh": "None.",
            "meds": "None.",
            "allergies": "No known drug allergies",
            "social": "High stress job, poor sleep hygiene",
        },
        "bruise": {
            "cc": "Bruise on left thigh after bumping into table",
            "hpi": "The patient presents with bruise on left thigh after bumping into table 2 days ago. Mild pain, no swelling. No bleeding disorders. No other bruising.",
            "pe": "- General: Well-appearing\n- Extremities: 5cm ecchymosis on left thigh, no swelling, no tenderness to palpation of bone",
            "additional": "No labs indicated\nDiagnosis: Simple contusion",
            "pmh": "None.",
            "meds": "None.",
            "allergies": "No known drug allergies",
            "social": "No significant history",
        },
        "contact_lens": {
            "cc": "Eye discomfort and redness with contact lens use",
            "hpi": "The patient presents with 1 day of right eye discomfort, redness, and foreign body sensation. Contact lens wearer, slept in lenses last night. No vision changes.",
            "pe": "- General: Well-appearing\n- Eyes: Right conjunctival injection, no corneal staining with fluorescein, visual acuity normal",
            "additional": "No labs indicated\nDiagnosis: Contact lens-related irritation",
            "pmh": "Myopia, contact lens wearer",
            "meds": "Artificial tears",
            "allergies": "No known drug allergies",
            "social": "Occasional overnight lens wear",
        },
    }

    t = templates[condition["template"]]

    common = dict(
        age=age, gender=gender, cc=t["cc"], hpi=t["hpi"],
        bp=vitals["bp"], hr=vitals["hr"], rr=vitals["rr"],
        spo2=vitals["spo2"], temp=vitals["temp"],
        pe=t["pe"], additional=t["additional"],
        pmh=t["pmh"], meds=t["meds"], allergies=t["allergies"],
        social=t.get("social", "Not recorded"),
    )

    template_map = {
        "senior_expressive": SENIOR_EXPRESSIVE,
        "senior_concise": SENIOR_CONCISE,
        "r1_expressive": R1_EXPRESSIVE,
        "r1_concise": R1_CONCISE,
        "senior_narrative": SENIOR_NARRATIVE,
        "r1_narrative": R1_NARRATIVE,
        "senior_stream": SENIOR_STREAM,
        "r1_stream": R1_STREAM,
        "senior_bullets": SENIOR_BULLETS,
        "r1_bullets": R1_BULLETS,
        "senior_soap": SENIOR_SOAP,
        "r1_soap": R1_SOAP,
    }

    text = template_map[profile].format(**common)

    if random.random() < 0.3:
        text = _shuffle_paragraphs(text)

    return text, condition["name"], priority, profile


def _shuffle_paragraphs(text):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) > 2:
        random.shuffle(paragraphs)
        return "\n\n".join(paragraphs)
    return text


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic triage reports.")
    parser.add_argument("--count", type=int, default=200, help="Number of reports to generate (default: 200).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible output (default: 42).")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "examples" / "cases",
        help="Directory in which to write reports.",
    )
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be greater than zero")

    random.seed(args.seed)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_profiles = Counter()
    generated_priorities = Counter()
    for i in range(args.count):
        text, condition_name, priority, profile = generate_case(i)
        filename = output_dir / f"case_{i+1:03d}_p{priority}_{profile}_{condition_name.lower().replace(' ', '_')}.txt"
        filename.write_text(text, encoding="utf-8")
        generated_profiles[profile] += 1
        generated_priorities[priority] += 1

    print(f"Generated {args.count} synthetic cases in {output_dir}")
    print(f"Profile distribution: {dict(sorted(generated_profiles.items()))}")
    print(f"ESI distribution: {dict(sorted(generated_priorities.items()))}")


if __name__ == "__main__":
    main()
