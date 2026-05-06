import streamlit as st
from ultralytics import YOLO
from PIL import Image
import datetime
import json
import io
import os
import random
import string
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

st.set_page_config(
    page_title="FMS50 – Fehlervisualisierung",
    page_icon="🔧",
    layout="wide"
)

# ─────────────────────────────────────────────
# Sprache
# ─────────────────────────────────────────────

TEXTE = {
    "DE": {
        "title": "FMS50 – Fehlervisualisierung Station 2",
        "step1": "1. Modul auswählen",
        "step2": "2. Bild hochladen oder Foto aufnehmen",
        "tab_upload": "Datei hochladen",
        "tab_camera": "Kamera",
        "step3": "3. SPS-Fehlercode auswählen",
        "step3b": "4. Betroffene Komponente auswählen",
        "step4": "5. Status festlegen",
        "step5": "6. Fehlerursache (optional)",
        "step6": "7. Bearbeiter (optional)",
        "step7": "8. Ersatzteile (optional)",
        "fehlerursache_placeholder": "Beschreibe die mögliche Fehlerursache...",
        "bearbeiter_placeholder": "Name des Technikers / Bearbeiters...",
        "ersatzteile_placeholder": "Verwendete Ersatzteile...",
        "btn_start": "Erkennung starten",
        "ergebnis": "Ergebnis",
        "erkanntes_modul": "Erkanntes Modul",
        "konfidenz": "Konfidenz",
        "betroffene_komponenten": "Betroffene Komponente auswählen",
        "loesungshinweis": "Lösungshinweis",
        "ticket": "Ticket",
        "export": "Export",
        "json_btn": "Als JSON exportieren",
        "pdf_btn": "Als PDF exportieren",
        "historie": "Wartungshistorie",
        "historie_leer": "Noch keine Tickets in dieser Sitzung.",
        "info_upload": "SPS-Code und Status auswählen, dann 'Erkennung starten' drücken.",
        "info_kein_bild": "Bitte ein Bild hochladen oder Foto aufnehmen.",
        "warning_nicht_erkannt": "Kein Modul erkannt. Bitte Bild oder Modell prüfen.",
        "fehler_modell": "Fehler beim Laden des Modells",
        "fehler_hinweis": "Stelle sicher, dass die .pt Datei im Ordner 'models/' liegt.",
        "status_offen": "Offen",
        "status_bearbeitung": "In Bearbeitung",
        "status_abgeschlossen": "Abgeschlossen",
        "nicht_definiert": "Nicht definiert",
        "ticket_felder": {
            "Ticket-Nr.": "Ticket-Nr.",
            "Zeitstempel": "Zeitstempel",
            "Station": "Station",
            "Modul": "Modul",
            "Komponente": "Komponente",
            "SPS-Code": "SPS-Code",
            "Fehlerbeschreibung": "Fehlerbeschreibung",
            "Fehlerursache": "Fehlerursache",
            "Bearbeiter": "Bearbeiter",
            "Ersatzteile": "Ersatzteile",
            "Konfidenz Erkennung": "Konfidenz Erkennung",
            "Status": "Status",
            "Status seit": "Status seit",
        },
        "station_name": "Station 2 – Bearbeitung (S02)",
        "footer": "FMS50-Anlage | FactoryLab FHWN | Station 2 – Bearbeitung (S02)",
        "kein_wert": "–",
        "nicht_erkannt": "nicht erkannt",
        "bounding_box": "Erkennungsergebnis mit Bounding Box",
    },
    "EN": {
        "title": "FMS50 – Fault Visualisation Station 2",
        "step1": "1. Select module",
        "step2": "2. Upload image or take photo",
        "tab_upload": "Upload file",
        "tab_camera": "Camera",
        "step3": "3. Select PLC error code",
        "step3b": "4. Select affected component",
        "step4": "5. Set status",
        "step5": "6. Error cause (optional)",
        "step6": "7. Technician (optional)",
        "step7": "8. Spare parts (optional)",
        "fehlerursache_placeholder": "Describe the possible error cause...",
        "bearbeiter_placeholder": "Name of technician...",
        "ersatzteile_placeholder": "Spare parts used...",
        "btn_start": "Start detection",
        "ergebnis": "Result",
        "erkanntes_modul": "Detected module",
        "konfidenz": "Confidence",
        "betroffene_komponenten": "Select affected component",
        "loesungshinweis": "Solution hint",
        "ticket": "Ticket",
        "export": "Export",
        "json_btn": "Export as JSON",
        "pdf_btn": "Export as PDF",
        "historie": "Maintenance history",
        "historie_leer": "No tickets in this session yet.",
        "info_upload": "Select PLC code and status, then press 'Start detection'.",
        "info_kein_bild": "Please upload an image or take a photo.",
        "warning_nicht_erkannt": "No module detected. Please check image or model.",
        "fehler_modell": "Error loading model",
        "fehler_hinweis": "Make sure the .pt file is in the 'models/' folder.",
        "status_offen": "Open",
        "status_bearbeitung": "In Progress",
        "status_abgeschlossen": "Closed",
        "nicht_definiert": "Not defined",
        "ticket_felder": {
            "Ticket-Nr.": "Ticket No.",
            "Zeitstempel": "Timestamp",
            "Station": "Station",
            "Modul": "Module",
            "Komponente": "Component",
            "SPS-Code": "PLC Code",
            "Fehlerbeschreibung": "Error description",
            "Fehlerursache": "Error cause",
            "Bearbeiter": "Technician",
            "Ersatzteile": "Spare parts",
            "Konfidenz Erkennung": "Detection confidence",
            "Status": "Status",
            "Status seit": "Status since",
        },
        "station_name": "Station 2 – Processing (S02)",
        "footer": "FMS50 System | FactoryLab FHWN | Station 2 – Processing (S02)",
        "kein_wert": "–",
        "nicht_erkannt": "not detected",
        "bounding_box": "Detection result with bounding box",
    },
}

# ─────────────────────────────────────────────
# Modul-Konfiguration
# TODO: Ersetzen durch GET /modules von Demirs Backend
# API_URL = "http://demirs-server:8000"
# ─────────────────────────────────────────────

MODELLE = {
    "DE": {
        "Modul 1 – Förderband-Schnittstelle": {
            "model_path": "models/modul1_best.pt",
            "klasse": "modul1",
            "sps_codes": [
                {"code": "E0.0", "beschreibung": "Induktiver Sensor – Kutsche nicht erkannt"},
                {"code": "E0.1", "beschreibung": "Lichtschranke – kein Werkstück auf Kutsche"},
                {"code": "A0.0", "beschreibung": "Stopper-Riegel – Endlage nicht erreicht"},
            ],
            "komponenten": ["Stopper-Riegel (pneumatisch)", "Magnetventil Stopper", "Induktiver Sensor (Kutsche)", "Lichtschranke (Werkstück)"],
            "solution": "Sichtprüfung der Förderband-Schnittstelle durchführen. Sensor auf Verschmutzung prüfen. Druckluftversorgung kontrollieren.",
        },
        "Modul 2 – PickAlfa": {
            "model_path": "models/modul2_best.pt",
            "klasse": "modul2",
            "sps_codes": [
                {"code": "E0.2", "beschreibung": "Linearachse – Endlage links nicht erreicht"},
                {"code": "E0.3", "beschreibung": "Linearachse – Endlage rechts nicht erreicht"},
                {"code": "E0.4", "beschreibung": "Hubzylinder – Endlage oben nicht erreicht"},
                {"code": "E0.5", "beschreibung": "Hubzylinder – Endlage unten nicht erreicht"},
                {"code": "E0.6", "beschreibung": "Greifer – Werkstück nicht gegriffen"},
            ],
            "komponenten": ["Pneumatische Linearachse (X)", "Hubzylinder (Z-Achse)", "Parallelgreifer", "Optischer Sensor (Greiferbacke)", "Endlagensensoren Linearachse (2×)", "Endlagensensoren Hubzylinder (2×)", "Drosselrückschlagventile", "Magnetventile PickAlfa (3×)", "Mechanische Endanschläge"],
            "solution": "Endlagensensoren auf korrekte Ausrichtung prüfen. Pneumatikversorgung und Magnetventile kontrollieren. Greiferfunktion manuell testen.",
        },
        "Modul 3 – Rundschalttisch": {
            "model_path": "models/modul3_best.pt",
            "klasse": "modul3",
            "sps_codes": [
                {"code": "E1.0", "beschreibung": "Rundschalttisch – Position nicht erreicht"},
                {"code": "E1.1", "beschreibung": "Kapazitiver Sensor – Werkstück fehlt"},
                {"code": "E1.2", "beschreibung": "Indexiereinheit – Rastposition nicht erkannt"},
            ],
            "komponenten": ["Antriebsmotor (elektrisch)", "Drehteller mit 6 Aufnahmen", "Indexiereinheit / Rastmechanismus", "Kapazitive Sensoren (3×)", "Induktiver Sensor (Position)", "Getriebe / Antriebsmechanik"],
            "solution": "Drehteller auf mechanische Blockierung prüfen. Indexiereinheit auf Verschleiß kontrollieren. Sensorpositionen prüfen.",
        },
        "Modul 5 – Bohrlochprüfung": {
            "model_path": "models/modul5_best.pt",
            "klasse": "modul5",
            "sps_codes": [
                {"code": "E1.4", "beschreibung": "Bohrlochprüfung – Bohrung nicht OK"},
                {"code": "E1.5", "beschreibung": "Prüfmagnet – Endlage nicht erreicht"},
            ],
            "komponenten": ["Prüfmagnet (elektromagnetisch)", "Sensorik Bohrlochprüfung", "Halterung / Führung Prüfmagnet"],
            "solution": "Prüfmagnet auf Verschleiß prüfen. Führungsbuchse kontrollieren. Sensor auf Signaldrift prüfen.",
        },
        "Modul 6 – Bohren": {
            "model_path": "models/modul6_best.pt",
            "klasse": "modul6",
            "sps_codes": [
                {"code": "E2.0", "beschreibung": "Bohrmotor – Übertemperatur"},
                {"code": "E2.1", "beschreibung": "Vorschub – Endlage unten nicht erreicht"},
                {"code": "E2.2", "beschreibung": "Vorschub – Endlage oben nicht erreicht"},
            ],
            "komponenten": ["Bohrmotor (elektrisch)", "Linearachse Zahnriemen (elektr.)", "Bohrer / Werkzeug", "Endlagensensor oben", "Endlagensensor unten", "Magnetventil Bohrvorschub"],
            "solution": "Bohrer auf Verschleiß prüfen. Motortemperatur kontrollieren. Endlagensensoren überprüfen.",
        },
        "Modul 7 – Spannen": {
            "model_path": "models/modul7_best.pt",
            "klasse": "modul7",
            "sps_codes": [
                {"code": "E2.3", "beschreibung": "Spannvorrichtung – Spannposition nicht erreicht"},
                {"code": "E2.4", "beschreibung": "Spannvorrichtung – Löseposition nicht erreicht"},
            ],
            "komponenten": ["Spannvorrichtung (elektrisch)", "Endlagensensor gespannt", "Endlagensensor gelöst", "Magnetventil Spannen"],
            "solution": "Spannmagnet auf Funktion prüfen. Endlagensensoren kontrollieren. Spannbacke auf Verschleiß prüfen.",
        },
        "Modul 8 – Steuerung & Bedienpult": {
            "model_path": "models/modul8_best.pt",
            "klasse": "modul8",
            "sps_codes": [
                {"code": "E3.0", "beschreibung": "SPS – E/A-Fehler"},
                {"code": "E3.1", "beschreibung": "Not-Aus – aktiviert"},
                {"code": "E3.2", "beschreibung": "Relais – Schaltfehler"},
            ],
            "komponenten": ["SPS (Siemens S7-200SP)", "E/A-Terminal", "Relais (5×)", "Bedienpult"],
            "solution": "SPS-Diagnosepuffer auslesen. E/A-Terminal und Steckverbindungen prüfen. Relais auf Kontaktverschleiß kontrollieren.",
        },
    },
    "EN": {
        "Module 1 – Conveyor Interface": {
            "model_path": "models/modul1_best.pt", "klasse": "modul1",
            "sps_codes": [{"code": "E0.0", "beschreibung": "Inductive sensor – carrier not detected"}, {"code": "E0.1", "beschreibung": "Light barrier – no workpiece on carrier"}, {"code": "A0.0", "beschreibung": "Stopper bolt – end position not reached"}],
            "komponenten": ["Stopper bolt (pneumatic)", "Solenoid valve stopper", "Inductive sensor (carrier)", "Light barrier (workpiece)"],
            "solution": "Visual inspection of conveyor interface. Check sensor for contamination. Verify compressed air supply.",
        },
        "Module 2 – PickAlfa": {
            "model_path": "models/modul2_best.pt", "klasse": "modul2",
            "sps_codes": [{"code": "E0.2", "beschreibung": "Linear axis – left end position not reached"}, {"code": "E0.3", "beschreibung": "Linear axis – right end position not reached"}, {"code": "E0.4", "beschreibung": "Lift cylinder – upper end position not reached"}, {"code": "E0.5", "beschreibung": "Lift cylinder – lower end position not reached"}, {"code": "E0.6", "beschreibung": "Gripper – workpiece not gripped"}],
            "komponenten": ["Pneumatic linear axis (X)", "Lift cylinder (Z-axis)", "Parallel gripper", "Optical sensor (gripper jaw)", "End position sensors linear axis (2×)", "End position sensors lift cylinder (2×)", "Throttle check valves", "Solenoid valves PickAlfa (3×)", "Mechanical end stops"],
            "solution": "Check end position sensors. Verify pneumatic supply and solenoid valves. Manually test gripper function.",
        },
        "Module 3 – Rotary indexing table": {
            "model_path": "models/modul3_best.pt", "klasse": "modul3",
            "sps_codes": [{"code": "E1.0", "beschreibung": "Rotary table – position not reached"}, {"code": "E1.1", "beschreibung": "Capacitive sensor – workpiece missing"}, {"code": "E1.2", "beschreibung": "Indexing unit – detent position not detected"}],
            "komponenten": ["Drive motor (electric)", "Rotary plate with 6 positions", "Indexing unit / detent mechanism", "Capacitive sensors (3×)", "Inductive sensor (position)", "Gearbox / drive mechanism"],
            "solution": "Check rotary table for mechanical blockage. Inspect indexing unit for wear. Verify sensor positions.",
        },
        "Module 5 – Bore hole inspection": {
            "model_path": "models/modul5_best.pt", "klasse": "modul5",
            "sps_codes": [{"code": "E1.4", "beschreibung": "Bore hole inspection – hole not OK"}, {"code": "E1.5", "beschreibung": "Test magnet – end position not reached"}],
            "komponenten": ["Test magnet (electromagnetic)", "Bore hole inspection sensor", "Mounting / guide test magnet"],
            "solution": "Check test magnet for wear. Inspect guide bushing. Check sensor for signal drift.",
        },
        "Module 6 – Drilling": {
            "model_path": "models/modul6_best.pt", "klasse": "modul6",
            "sps_codes": [{"code": "E2.0", "beschreibung": "Drill motor – overtemperature"}, {"code": "E2.1", "beschreibung": "Feed axis – lower end position not reached"}, {"code": "E2.2", "beschreibung": "Feed axis – upper end position not reached"}],
            "komponenten": ["Drill motor (electric)", "Linear axis toothed belt (electric)", "Drill bit / tool", "End position sensor top", "End position sensor bottom", "Solenoid valve drill feed"],
            "solution": "Check drill bit for wear. Monitor motor temperature. Check end position sensors.",
        },
        "Module 7 – Clamping": {
            "model_path": "models/modul7_best.pt", "klasse": "modul7",
            "sps_codes": [{"code": "E2.3", "beschreibung": "Clamping device – clamp position not reached"}, {"code": "E2.4", "beschreibung": "Clamping device – release position not reached"}],
            "komponenten": ["Clamping device (electric)", "End position sensor clamped", "End position sensor released", "Solenoid valve clamping"],
            "solution": "Check clamping magnet function. Inspect end position sensors. Check clamping jaw for wear.",
        },
        "Module 8 – Control & operator panel": {
            "model_path": "models/modul8_best.pt", "klasse": "modul8",
            "sps_codes": [{"code": "E3.0", "beschreibung": "PLC – I/O error"}, {"code": "E3.1", "beschreibung": "Emergency stop – activated"}, {"code": "E3.2", "beschreibung": "Relay – switching error"}],
            "komponenten": ["PLC (Siemens S7-200SP)", "I/O terminal", "Relays (5×)", "Operator panel"],
            "solution": "Read PLC diagnostic buffer. Check I/O terminal and connectors. Inspect relays for contact wear.",
        },
    },
}

STATUS_FARBEN = {
    "DE": {"Offen": ("🔴", "#E24B4A"), "In Bearbeitung": ("🟡", "#EF9F27"), "Abgeschlossen": ("🟢", "#1D9E75")},
    "EN": {"Open": ("🔴", "#E24B4A"), "In Progress": ("🟡", "#EF9F27"), "Closed": ("🟢", "#1D9E75")},
}

HISTORIE_DATEI = "wartungshistorie.json"

def generiere_ticket_nr():
    datum = datetime.datetime.now().strftime("%Y%m%d")
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"TKT-{datum}-{suffix}"

def lade_historie():
    if os.path.exists(HISTORIE_DATEI):
        try:
            with open(HISTORIE_DATEI, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def speichere_historie(ticket):
    historie = lade_historie()
    historie.append(ticket)
    with open(HISTORIE_DATEI, "w", encoding="utf-8") as f:
        json.dump(historie, f, ensure_ascii=False, indent=2)

def erstelle_pdf(ticket, komponenten, solution, felder, bild_pil=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    style_title   = ParagraphStyle("t",   fontSize=18, fontName="Helvetica-Bold", spaceAfter=4,  textColor=colors.HexColor("#185FA5"))
    style_sub     = ParagraphStyle("s",   fontSize=10, fontName="Helvetica",      spaceAfter=16, textColor=colors.HexColor("#888780"))
    style_section = ParagraphStyle("sec", fontSize=12, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#2C2C2A"))
    style_body    = ParagraphStyle("b",   fontSize=10, fontName="Helvetica",      spaceAfter=4,  textColor=colors.HexColor("#2C2C2A"))
    style_sol     = ParagraphStyle("sol", fontSize=10, fontName="Helvetica",      spaceAfter=4,  textColor=colors.HexColor("#185FA5"), backColor=colors.HexColor("#E6F1FB"), leftIndent=8, rightIndent=8, spaceBefore=4)

    status_farbe_map = {"Offen": colors.HexColor("#E24B4A"), "In Bearbeitung": colors.HexColor("#EF9F27"), "Abgeschlossen": colors.HexColor("#1D9E75"), "Open": colors.HexColor("#E24B4A"), "In Progress": colors.HexColor("#EF9F27"), "Closed": colors.HexColor("#1D9E75")}
    status_farbe = status_farbe_map.get(ticket.get(felder["Status"], ""), colors.black)

    elemente = []
    elemente.append(Paragraph(ticket.get("_pdf_title", "FMS50"), style_title))
    elemente.append(Paragraph(ticket.get("_pdf_footer", ""), style_sub))
    elemente.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D3D1C7")))
    elemente.append(Spacer(1, 0.4*cm))

    if bild_pil:
        from reportlab.platypus import Image as RLImage
        ib = io.BytesIO()
        bild_pil.save(ib, format="JPEG")
        ib.seek(0)
        elemente.append(RLImage(ib, width=10*cm, height=7*cm, kind="proportional"))
        elemente.append(Spacer(1, 0.3*cm))

    elemente.append(Paragraph(felder.get("ticket_heading", "Ticket"), style_section))

    ticket_keys = ["Ticket-Nr.", "Zeitstempel", "Station", "Modul", "Komponente", "SPS-Code",
                   "Fehlerbeschreibung", "Fehlerursache", "Bearbeiter", "Ersatzteile",
                   "Konfidenz Erkennung", "Status", "Status seit"]
    daten = [[felder.get(k, k), ticket.get(felder.get(k, k), "–")] for k in ticket_keys]

    tabelle = Table(daten, colWidths=[5*cm, 11.7*cm])
    tabelle.setStyle(TableStyle([
        ("FONTNAME",       (0,0),(0,-1), "Helvetica-Bold"),
        ("FONTNAME",       (1,0),(1,-1), "Helvetica"),
        ("FONTSIZE",       (0,0),(-1,-1), 10),
        ("TEXTCOLOR",      (0,0),(0,-1),  colors.HexColor("#5F5E5A")),
        ("TEXTCOLOR",      (1,0),(1,-1),  colors.HexColor("#2C2C2A")),
        ("TEXTCOLOR",      (1,11),(1,11), status_farbe),
        ("FONTNAME",       (1,11),(1,11), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,0),(-1,-1), [colors.HexColor("#F1EFE8"), colors.white]),
        ("TOPPADDING",     (0,0),(-1,-1), 6),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 6),
        ("LEFTPADDING",    (0,0),(-1,-1), 8),
        ("GRID",           (0,0),(-1,-1), 0.3, colors.HexColor("#D3D1C7")),
    ]))
    elemente.append(tabelle)
    elemente.append(Spacer(1, 0.4*cm))

    elemente.append(Paragraph(felder.get("komponenten_heading", "Komponenten"), style_section))
    for k in komponenten:
        elemente.append(Paragraph(f"• {k}", style_body))
    elemente.append(Spacer(1, 0.3*cm))

    elemente.append(Paragraph(felder.get("solution_heading", "Lösungshinweis"), style_section))
    elemente.append(Paragraph(solution, style_sol))

    doc.build(elemente)
    buffer.seek(0)
    return buffer

@st.cache_resource
def load_model(path):
    return YOLO(path)

# ─────────────────────────────────────────────
# Sprache & Session
# ─────────────────────────────────────────────

sprache = st.sidebar.radio("🌐 Language / Sprache", ["DE", "EN"], horizontal=True)
T  = TEXTE[sprache]
M  = MODELLE[sprache]
SF = STATUS_FARBEN[sprache]
status_optionen = list(SF.keys())

if "erkennungs_ergebnis" not in st.session_state:
    st.session_state.erkennungs_ergebnis = None

# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────

st.title(T["title"])
st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(T["step1"])
    modul_auswahl = st.selectbox("Modul", options=list(M.keys()), label_visibility="collapsed")
    modul_info = M[modul_auswahl]

    st.subheader(T["step2"])
    upload_tab, kamera_tab = st.tabs([T["tab_upload"], T["tab_camera"]])
    with upload_tab:
        uploaded_file = st.file_uploader("Bild", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    with kamera_tab:
        kamera_bild = st.camera_input("Foto", label_visibility="collapsed")
    bild_quelle = kamera_bild if kamera_bild is not None else uploaded_file

    st.subheader(T["step3"])
    sps_optionen = [f"{s['code']} – {s['beschreibung']}" for s in modul_info["sps_codes"]]
    sps_auswahl = st.selectbox("SPS", options=sps_optionen, label_visibility="collapsed")

    st.subheader(T["step3b"])
    komp_optionen = [T["nicht_definiert"]] + modul_info["komponenten"]
    komp_auswahl = st.selectbox("Komponente", options=komp_optionen, label_visibility="collapsed")

    st.subheader(T["step4"])
    status_auswahl = st.selectbox("Status", options=status_optionen, label_visibility="collapsed")
    emoji, farbe = SF[status_auswahl]
    st.markdown(f'<span style="color:{farbe}; font-weight:600; font-size:16px">{emoji} {status_auswahl}</span>', unsafe_allow_html=True)

    st.subheader(T["step5"])
    fehlerursache = st.text_area("Fehlerursache", placeholder=T["fehlerursache_placeholder"], label_visibility="collapsed", height=80)

    st.subheader(T["step6"])
    bearbeiter = st.text_input("Bearbeiter", placeholder=T["bearbeiter_placeholder"], label_visibility="collapsed")

    st.subheader(T["step7"])
    ersatzteile = st.text_area("Ersatzteile", placeholder=T["ersatzteile_placeholder"], label_visibility="collapsed", height=80)

    erkennung_starten = st.button(T["btn_start"], type="primary", use_container_width=True)

with col2:
    st.subheader(T["ergebnis"])

    if bild_quelle is not None and erkennung_starten:
        image = Image.open(bild_quelle).convert("RGB")
        with st.spinner("..."):
            try:
                model = load_model(modul_info["model_path"])
                results = model(image)
                result_img = results[0].plot()
                result_img_pil = Image.fromarray(result_img)
                detektionen = results[0].boxes
                anzahl = len(detektionen) if detektionen is not None else 0

                st.image(result_img_pil, caption=T["bounding_box"], use_container_width=True)
                st.divider()

                conf = float(detektionen.conf[0]) if anzahl > 0 else 0.0
                if anzahl > 0:
                    sc = "green" if conf >= 0.8 else "orange"
                    st.markdown(f"**{T['erkanntes_modul']}:** {modul_auswahl}")
                    st.markdown(f"**{T['konfidenz']}:** :{sc}[{conf:.2%}]")
                else:
                    st.warning(T["warning_nicht_erkannt"])

                sps_code = sps_auswahl.split(" – ")[0]
                sps_text = " – ".join(sps_auswahl.split(" – ")[1:])
                zeitstempel = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ticket_nr = generiere_ticket_nr()
                tf = T["ticket_felder"]

                st.divider()
                st.subheader(T["loesungshinweis"])
                st.info(modul_info["solution"])

                st.divider()
                st.subheader(T["ticket"])

                ticket = {
                    tf["Ticket-Nr."]:          ticket_nr,
                    tf["Zeitstempel"]:         zeitstempel,
                    tf["Station"]:             T["station_name"],
                    tf["Modul"]:               modul_auswahl,
                    tf["Komponente"]:          komp_auswahl,
                    tf["SPS-Code"]:            sps_code,
                    tf["Fehlerbeschreibung"]:  sps_text,
                    tf["Fehlerursache"]:       fehlerursache if fehlerursache else T["kein_wert"],
                    tf["Bearbeiter"]:          bearbeiter if bearbeiter else T["kein_wert"],
                    tf["Ersatzteile"]:         ersatzteile if ersatzteile else T["kein_wert"],
                    tf["Konfidenz Erkennung"]: f"{conf:.2%}" if anzahl > 0 else T["nicht_erkannt"],
                    tf["Status"]:              status_auswahl,
                    tf["Status seit"]:         zeitstempel,
                    "_pdf_title":              T["title"],
                    "_pdf_footer":             T["footer"],
                }

                for key, value in ticket.items():
                    if key.startswith("_"):
                        continue
                    if key == tf["Status"]:
                        e, f = SF[value]
                        st.markdown(f'**{key}:** <span style="color:{f}; font-weight:600">{e} {value}</span>', unsafe_allow_html=True)
                    elif key == tf["Status seit"]:
                        e, f = SF.get(status_auswahl, ("⚪", "#888780"))
                        st.markdown(f'**{key}:** <span style="color:{f}; font-weight:600">{value}</span>', unsafe_allow_html=True)
                    elif key == tf["Zeitstempel"]:
                        st.markdown(f'**{key}:** <span style="color:#185FA5; font-weight:600">{value}</span>', unsafe_allow_html=True)
                    elif key == tf["Konfidenz Erkennung"]:
                        kf = "#1D9E75" if conf >= 0.8 else "#EF9F27"
                        st.markdown(f'**{key}:** <span style="color:{kf}; font-weight:600">{value}</span>', unsafe_allow_html=True)
                    elif key == tf["Ticket-Nr."]:
                        st.markdown(f'**{key}:** `{value}`')
                    else:
                        st.markdown(f"**{key}:** {value}")

                # In Historie speichern
                # TODO: Ticket zusätzlich an Demirs Backend senden
                # requests.post(f"{API_URL}/tickets", json=ticket)
                speichere_historie({k: v for k, v in ticket.items() if not k.startswith("_")})

                st.divider()
                st.subheader(T["export"])

                ticket_export = {k: v for k, v in ticket.items() if not k.startswith("_")}
                ticket_json = json.dumps(ticket_export, ensure_ascii=False, indent=2)
                st.download_button(label=T["json_btn"], data=ticket_json,
                    file_name=f"{ticket_nr}.json", mime="application/json", use_container_width=True)

                pdf_felder = {**tf, "ticket_heading": T["ticket"], "komponenten_heading": T["betroffene_komponenten"], "solution_heading": T["loesungshinweis"]}
                pdf_buffer = erstelle_pdf(ticket, modul_info["komponenten"], modul_info["solution"], pdf_felder, bild_pil=result_img_pil)
                st.download_button(label=T["pdf_btn"], data=pdf_buffer,
                    file_name=f"{ticket_nr}.pdf", mime="application/pdf", use_container_width=True)

            except Exception as e:
                st.error(f"{T['fehler_modell']}: {e}")
                st.info(T["fehler_hinweis"])

    elif bild_quelle is not None:
        image = Image.open(bild_quelle)
        st.image(image, use_container_width=True)
        st.info(T["info_upload"])
    else:
        st.info(T["info_kein_bild"])

# ─────────────────────────────────────────────
# Wartungshistorie
# ─────────────────────────────────────────────

st.divider()
st.subheader(T["historie"])

historie = lade_historie()
if not historie:
    st.info(T["historie_leer"])
else:
    for eintrag in reversed(historie):
        tf = T["ticket_felder"]
        status_val = eintrag.get(tf["Status"], "–")
        e, f = SF.get(status_val, ("⚪", "#888780"))
        with st.expander(f'{eintrag.get(tf["Ticket-Nr."], "–")} · {eintrag.get(tf["Modul"], "–")} · {e} {status_val} · {eintrag.get(tf["Zeitstempel"], "–")}'):
            for k, v in eintrag.items():
                if k == tf["Status"]:
                    st.markdown(f'**{k}:** <span style="color:{f}; font-weight:600">{e} {v}</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f"**{k}:** {v}")

st.divider()
st.caption(T["footer"])
