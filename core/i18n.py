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
    "DEL": "DELETE",
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
    "RIGENERA PDF": "REGENERATE PDF",
    "Successo": "Success",
    "Report PDF rigenerato con successo.": "PDF report successfully regenerated.",
    "Impossibile generare il PDF": "Unable to generate PDF",
    "Conferma eliminazione": "Confirm deletion",
    "Sei sicuro di voler eliminare il report selezionato? L'operazione è irreversibile.": "Are you sure you want to delete the selected report? This operation is irreversible.",
    
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

    # ── Taratura / cella di carico ──
    "TARATURA IN CORSO": "TARING",
    "RITORNO A ZERO — ATTENDERE {s} s": "RETURN TO ZERO — WAIT {s} s",
    "PAUSA": "PAUSE",
    "PAUSA TRA PEZZI": "PAUSE BETWEEN PIECES",
    "La pausa tra pezzi non può essere negativa.": "The pause between pieces cannot be negative.",
    "ATTESA RITORNO A ZERO": "WAITING FOR RETURN TO ZERO",
    "ATTESA ZERO (± {t} mN) — SCARICARE LA CELLA": "WAITING FOR ZERO (± {t} mN) — UNLOAD THE CELL",
    "TOLLERANZA ZERO": "ZERO TOLERANCE",
    "La tolleranza dello zero deve essere maggiore di 0.": "The zero tolerance must be greater than 0.",
    "TARATURA IN CORSO — non toccare l'attrezzatura": "TARING — do not touch the fixture",
    "Taratura non riuscita: collaudo annullato. Controllare la cella di carico.": "Tare failed: inspection cancelled. Check the load cell.",
    "Taratura non riuscita": "Tare failed",
    "Calibrazione non riuscita": "Calibration failed",
    "Cella di carico non pronta: nuovo tentativo in corso...": "Load cell not ready: retrying...",
    "La cella di carico non risponde": "The load cell is not responding",
    "Fattore di calibrazione non inviato alla scheda": "Calibration factor not sent to the board",

    # ── Calibration Page ──
    "CALIBRAZIONE CELLA": "LOAD CELL CALIBRATION",
    "CALIBRAZIONE CELLA DI CARICO": "LOAD CELL CALIBRATION",
    "1 · Togliere tutto dalla cella e premere TARA A VUOTO": "1 · Remove everything from the load cell and press EMPTY TARE",
    "2 · Appoggiare il peso, inserire la massa e premere CALIBRA": "2 · Place the weight, enter its mass and press CALIBRATE",
    "3 · Verificare il valore atteso, poi togliere il peso: deve tornare a 0": "3 · Check the expected value, then remove the weight: it must return to 0",
    "MASSA DI RIFERIMENTO": "REFERENCE MASS",
    "TARA A VUOTO": "EMPTY TARE",
    "CALIBRA CON IL PESO": "CALIBRATE WITH WEIGHT",
    "Premere TARA A VUOTO con la cella libera.": "Press EMPTY TARE with nothing on the load cell.",
    "Tara in corso — non toccare la cella...": "Taring — do not touch the load cell...",
    "Calibrazione in corso — non toccare il peso...": "Calibrating — do not touch the weight...",
    "Inserire una massa valida in grammi.": "Enter a valid mass in grams.",
    "Tara completata. Appoggiare il peso e premere CALIBRA.": "Tare done. Place the weight and press CALIBRATE.",
    "Tara non riuscita: controllare la cella di carico.": "Tare failed: check the load cell.",
    "Calibrazione salvata. Valore atteso": "Calibration saved. Expected value",
    "togliendo il peso deve tornare a 0.": "removing the weight it must return to 0.",
    "Calibrazione non riuscita: peso non appoggiato o cella non pronta.": "Calibration failed: weight not placed or load cell not ready.",
    "Cella non calibrata: la forza è in conteggi ADC, non in mN": "Load cell not calibrated: force is in ADC counts, not mN",
    "Fattore": "Factor",
    "conteggio": "count",
    "Ultima calibrazione": "Last calibration",

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
