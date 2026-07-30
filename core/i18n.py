"""
i18n.py
-------
Semplice modulo per la traduzione e localizzazione (i18n) dell'interfaccia utente.
Supporta Italiano ("it") e Inglese ("en").
"""

from config import Config

_EN_DICT = {
    # ── Menu / NavBar ──
    "HOME": "HOME",
    "NUOVO TEST": "NEW TEST",
    "STORICO": "HISTORY",
    "IMPOSTAZIONI": "SETTINGS",
    
    # ── Test Controller ──
    "Un collaudo è già in corso.": "An inspection is already in progress.",
    "ACQUISIZIONE PEZZO": "ACQUIRING PIECE",
    "Nessun campione acquisito per questo pezzo.": "No samples acquired for this piece.",
    
    # ── Main Window ──
    "Errore": "Error",
    "ATTESA TRIGGER...": "WAITING FOR TRIGGER...",
    "OK ✓": "OK ✓",
    "FUORI LIMITE ✗": "OUT OF LIMIT ✗",
    "Pezzo": "Piece",
    "Sessione completata": "Session completed",
    "Risultato": "Result",
    "Pezzi": "Pieces",
    "Accesso protetto": "Protected access",
    "Inserire la password:": "Enter password:",
    "Accesso negato": "Access denied",
    "Password errata.": "Incorrect password.",
    
    # ── Home Page ──
    "BENVENUTO": "WELCOME",
    "Seleziona un'operazione dal menu laterale.": "Select an operation from the side menu.",
    "Macchinario Pronto": "Machine Ready",
    "Sistema di Acquisizione Operativo": "Acquisition System Operational",
    "ELASTIC REACTION TEST": "ELASTIC REACTION TEST",
    "PF0924 — Controllo Forza di Reazione Elastica": "PF0924 — Elastic Reaction Force Control",
    "TEST": "TEST",
    "Avvia una nuova sessione di collaudo": "Start a new inspection session",
    "SETTING": "SETTING",
    "Accedi alle impostazioni (richiede password)": "Access settings (password required)",
    "STORICO DATI": "INSPECTION HISTORY",
    "Visualizza lo storico dei collaudi": "View the inspection history",
    "Versione 1.0.0  ·  IDT Solution S.r.l.s.b.": "Version 1.0.0 · IDT Solution S.r.l.s.b.",
    
    # ── New Test Page ──
    "IMPOSTA COLLAUDO": "SET UP INSPECTION",
    "Inserire i dati prima di avviare il collaudo": "Enter data before starting the inspection",
    "Codice Operatore": "Operator Code",
    "Codice Stampo": "Mould Code",
    "Lotto Produzione": "Production Lot",
    "Lotto Materia Prima": "Raw Material Lot",
    "AVVIA COLLAUDO": "START INSPECTION",
    "OPERATORE": "OPERATOR",
    "STAMPO": "MOULD",
    "LOTTO PRODUZIONE": "PRODUCTION LOT",
    "MATERIA PRIMA": "RAW MATERIAL",
    "OPERATORE": "OPERATOR",
    "STAMPO": "MOULD",
    "Forza in Tempo Reale": "Real Time Force",
    "TERMINA COLLAUDO": "END INSPECTION",
    "ATTESA TRIGGER": "WAITING FOR TRIGGER",
    "ACQUISIZIONE IN CORSO": "ACQUISITION IN PROGRESS",
    
    # ── History Page ──
    "STORICO COLLAUDI": "INSPECTION HISTORY",
    "Collaudi precedenti — clicca VIEW per aprire il report PDF": "Previous inspections — click VIEW to open PDF report",
    "VIEW": "VIEW",
    "DATA": "DATE",
    "REPORT": "REPORT",
    
    # ── Report Page ──
    "ELASTIC REACTION TEST REPORT": "ELASTIC REACTION TEST REPORT",
    "DATE": "DATE",
    "PRODUCTION LOT": "PRODUCTION LOT",
    "RAW MATERIAL LOT": "RAW MATERIAL LOT",
    "LOWER SPEC LIMIT": "LOWER SPEC LIMIT",
    "UPPER SPEC LIMIT": "UPPER SPEC LIMIT",
    "MIN DETECTED VALUE": "MIN DETECTED VALUE",
    "MEAN VALUE": "MEAN VALUE",
    "MAX DETECTED VALUE": "MAX DETECTED VALUE",
    "STANDARD DEVIATION": "STANDARD DEVIATION",
    "INSPECTION RESULT": "INSPECTION RESULT",
    
    # ── Settings Page ──
    "IMPOSTAZIONI DI SISTEMA": "SYSTEM SETTINGS",
    "Modifica i parametri di collaudo  ·  Accesso protetto": "Modify inspection parameters · Protected access",
    "Parametri di Acquisizione": "Acquisition Parameters",
    "Frequenza di Campionamento (Hz)": "Sampling Rate (Hz)",
    "Tempo di Collaudo (sec)": "Inspection Time (sec)",
    "Forza di Trigger (mN)": "Trigger Force (mN)",
    "Limiti di Specifica": "Specification Limits",
    "Limite Inferiore - LSL (mN)": "Lower Limit - LSL (mN)",
    "Limite Superiore - USL (mN)": "Upper Limit - USL (mN)",
    "Interfaccia": "Interface",
    "Lingua di Sistema": "System Language",
    "SALVA IMPOSTAZIONI": "SAVE SETTINGS",
    "LIMITE INFERIORE": "LOWER LIMIT",
    "LIMITE SUPERIORE": "UPPER LIMIT",
    "TEMPO": "TIME",
    "FORZA TRIGGER": "TRIGGER FORCE",
    
    # ── Status Widget ──
    "Sistema pronto": "System ready",
    "CELLA DI CARICO": "LOAD CELL",
    
    # ── Generici ──
    "Connesso": "Connected",
    "Non Connesso": "Disconnected",
    "Errore": "Error",
    "Valori non validi. Inserire solo numeri.": "Invalid values. Enter numbers only.",
    "Salvataggio": "Save",
    "Impostazioni salvate con successo.": "Settings saved successfully.",
    "Per applicare il cambio di lingua, riavviare l'applicazione.": "To apply the language change, please restart the application.",
    "INDIETRO": "BACK",
}

def _(text: str) -> str:
    """
    Traduce il testo in base a Config.language.
    Se la lingua è 'it' restituisce il testo originale.
    Se la lingua è 'en' cerca nel dizionario.
    """
    lang = Config.language.lower()
    if lang == "en":
        return _EN_DICT.get(text, text)
    return text
