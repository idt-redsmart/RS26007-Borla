import os
from pathlib import Path
from datetime import datetime
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

# Costanti layout A4
WIDTH, HEIGHT = A4
MARGIN = 10 * mm

def _generate_chart(samples: list, lsl: float, usl: float, title: str) -> io.BytesIO:
    """Genera il grafico di trend in memoria con sfondo bianco e asse X visibile."""
    # Sfondo bianco per il PDF
    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor='white')
    ax.set_facecolor("white")
    
    # Colori scuri per il contrasto su carta
    ui_text_color = "#222222"
    ui_line_color = "#ed7d31" # Torniamo ad arancio per la linea dati su bianco
    ui_limit_color = "#00b050" # Verde per i limiti

    # Stile bordi
    for spine in ax.spines.values():
        spine.set_color("#cccccc")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Griglia orizzontale morbida
    ax.grid(True, linestyle='--', alpha=0.5, color='#dddddd')
    ax.set_axisbelow(True)
    
    # Titolo ed etichette
    ax.set_title(title, color=ui_text_color, fontsize=13, fontweight='bold', pad=20, fontfamily='sans-serif')
    ax.set_ylabel("ELASTIC REACTION [mN]", color=ui_text_color, fontsize=10, fontweight='bold', labelpad=10)
    ax.set_xlabel("CAMPIONI", color=ui_text_color, fontsize=10, fontweight='bold', labelpad=10)
    ax.tick_params(colors=ui_text_color, length=4)
    
    # Asse X visibile
    ax.tick_params(axis='x', which='both', bottom=True, top=False, labelbottom=True)

    x = list(range(1, len(samples) + 1))
    y = samples

    # Linee LSL / USL tratteggiate verdi come richiesto in origine
    ax.axhline(lsl, color=ui_limit_color, linewidth=1.5, linestyle='--', zorder=2)
    ax.axhline(usl, color=ui_limit_color, linewidth=1.5, linestyle='--', zorder=2)
    
    # Testo LSL e USL
    ax.text(0.01, lsl, "LSL", color=ui_limit_color, transform=ax.get_yaxis_transform(), va="bottom", fontsize=9, fontweight='bold')
    ax.text(0.01, usl, "USL", color=ui_limit_color, transform=ax.get_yaxis_transform(), va="bottom", fontsize=9, fontweight='bold')

    # Dati: linea principale
    if samples:
        ax.plot(x, y, color=ui_line_color, linewidth=2.5, zorder=3,
                marker='o', markersize=6, markerfacecolor='white', markeredgewidth=2)
        # Sfumatura sotto la linea
        y_min = max(0, min(lsl, min(y)) - (usl - lsl) * 0.3) if y else lsl - (usl - lsl) * 0.3
        ax.fill_between(x, y, y_min, color=ui_line_color, alpha=0.1, zorder=2)

    # Calcolo dei limiti ottimali per l'asse Y
    margin = (usl - lsl) * 0.4
    y_min_lim = max(0, min(lsl - margin, min(y) - margin * 0.5) if y else lsl - margin)
    y_max_lim = max(usl + margin, max(y) + margin * 0.5) if y else usl + margin
    
    # Ticks Y dinamici ma eleganti
    import matplotlib.ticker as ticker
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
    ax.set_ylim(y_min_lim, y_max_lim)

    # Asse X con ticks interi interi per i campioni
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # Margini del layout
    plt.tight_layout()

    buf = io.BytesIO()
    # Sfondo bianco per la stampa
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_report(data: dict, reports_dir: str) -> str:
    """
    Genera il PDF finale e lo salva nella cartella reports.
    Ritorna il path assoluto del PDF generato.
    """
    Path(reports_dir).mkdir(parents=True, exist_ok=True)
    
    # Il formato richiesto per DATE nella tabella è dd.mmm.yyyy
    date_obj = datetime.now()
    if data.get("date"):
        try:
            date_obj = datetime.fromisoformat(data["date"])
        except:
            pass
            
    mesi = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
    date_short = f"{date_obj.day:02d}.{mesi[date_obj.month-1]}.{date_obj.year}"
    date_file = date_obj.strftime("%Y%m%d_%H%M%S")
    
    mould = str(data.get("mould", "N-A")).replace("/", "-")
    test_id = data.get("id", "0")
    part_number = data.get("part_number", "PF0924")
    
    filename = f"Report_{mould}_{date_file}.pdf"
    filepath = os.path.join(reports_dir, filename)

    c = canvas.Canvas(filepath, pagesize=A4)
    c.setLineWidth(1)
    
    # ─── Bordo Esterno Completo ───
    # Come in foto: c'è un box rettangolare che circonda tutto
    c.rect(MARGIN, MARGIN, WIDTH - 2*MARGIN, HEIGHT - 2*MARGIN)

    # ─── HEADER ───
    c.setFont("Helvetica", 10)
    c.drawCentredString(WIDTH / 2, HEIGHT - MARGIN - 12, "Industrie Borla srl")
    
    # ─── LOGO CLIENTE (alto a sinistra) ──────────────────────────────────────
    from config import Config as _Cfg
    from reportlab.lib.utils import ImageReader as _ImgReader
    _logo_path = _Cfg.logo_path
    if _logo_path is not None:
        try:
            _logo_pix = _ImgReader(str(_logo_path))
            _lw, _lh  = _logo_pix.getSize()
            # Scala mantenendo aspect ratio, molto più piccolo per non coprire i testi
            _max_h = 12 * mm
            _max_w = 40 * mm
            _scale = min(_max_h / _lh, _max_w / _lw)
            _draw_w, _draw_h = _lw * _scale, _lh * _scale
            _logo_x = MARGIN + 2 * mm
            # La linea orizzontale è a HEIGHT - MARGIN - 18. Posizioniamo il logo appena sotto di essa.
            _logo_y = HEIGHT - MARGIN - 18 - _draw_h - 2 * mm
            c.drawImage(_logo_pix, _logo_x, _logo_y,
                        width=_draw_w, height=_draw_h, mask="auto")
        except Exception:
            pass  # fallback silenzioso: solo testo
    # ─────────────────────────────────────────────────────────────────────────

    
    c.line(MARGIN, HEIGHT - MARGIN - 18, WIDTH - MARGIN, HEIGHT - MARGIN - 18)


    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(WIDTH / 2, HEIGHT - MARGIN - 50, "ELASTIC REACTION TEST REPORT")
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(WIDTH / 2, HEIGHT - MARGIN - 75, str(part_number))

    # ─── TABELLA DATI (sinistra) ───
    # Da y = HEIGHT - MARGIN - 90 in giù
    table_data = [
        ["DATE", date_short],
        ["OPERATOR", data.get("operator", "")],
        ["MOULD", data.get("mould", "")],
        ["RAW MATERIAL LOT", data.get("raw_material_lot", "")],
        ["PRODUCTION LOT", data.get("production_lot", "")],
        ["QTY", str(data.get("qty", 0))],
        ["LOWER SPEC LIMIT", f"{data.get('lower_limit', 0):.0f}     mN"],
        ["UPPER SPEC LIMIT", f"{data.get('upper_limit', 0):.0f}     mN"],
        ["MIN DETECTED\nVALUE", f"{data.get('min_mn', 0):.0f}     mN"],
        ["MEAN VALUE", f"{data.get('mean_mn', 0):.0f}     mN"],
        ["MAX DETECTED\nVALUE", f"{data.get('max_mn', 0):.0f}     mN"],
        ["RANGE", f"{data.get('range_mn', 0):.0f}     mN"],
        ["STANDARD\nDEVIATION", f"{data.get('std_mn', 0):.1f}     mN"],
    ]
    
    col_widths = [45*mm, 45*mm]
    # Riduco l'altezza delle righe per dare più spazio verticale al grafico
    t = Table(table_data, colWidths=col_widths, rowHeights=10.5*mm)
    
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    
    # Sovrascriviamo le righe interne orizzontali per essere tratteggiate
    for r in range(1, len(table_data)):
        t.setStyle(TableStyle([
            ('LINEABOVE', (0, r), (1, r), 0.5, colors.black, None, (2,2)) # tratteggio
        ]))
    
    # Ma la cornice esterna della tabella e la linea verticale centrale devono essere continue
    t.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('LINEBEFORE', (1,0), (1,-1), 1, colors.black),
    ]))
    
    w, h = t.wrap(WIDTH, HEIGHT)
    table_x = MARGIN
    table_y = HEIGHT - MARGIN - 90 - h
    t.drawOn(c, table_x, table_y)

    # ─── GRAFICO (destra) ───
    # Estrarre force_values dai samples
    samples = data.get("samples", [])
    force_values = []
    for s in samples:
        if isinstance(s, dict) and "force_mn" in s:
            force_values.append(s["force_mn"])
        elif isinstance(s, (int, float)):
            force_values.append(s)

    lsl = data.get("lower_limit", 1060)
    usl = data.get("upper_limit", 1350)
    
    chart_title = f"{data.get('mould', '')} - Lot no. {data.get('production_lot', '')}"
    buf = _generate_chart(force_values, lsl, usl, chart_title)
    
    # Aggiungiamo un padding interno (es. 10 mm) rispetto al bordo esterno della pagina
    chart_pad = 10 * mm
    chart_x = MARGIN + chart_pad
    chart_y = MARGIN + 48*mm
    chart_w = WIDTH - 2*MARGIN - 2*chart_pad
    chart_h = table_y - chart_y - 5*mm
    
    # Disegna un bordino leggero attorno al grafico come in foto
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.rect(chart_x, chart_y, chart_w, chart_h)
    
    # Inserisci immagine
    from reportlab.lib.utils import ImageReader
    img = ImageReader(buf)
    c.drawImage(img, chart_x + 1*mm, chart_y + 1*mm, width=chart_w - 2*mm, height=chart_h - 2*mm, mask='auto')
    
    c.setStrokeColorRGB(0, 0, 0) # reset stroke

    # ─── INSPECTION RESULT ───
    res_x = MARGIN
    res_y = MARGIN + 25*mm
    res_w = 90*mm
    res_h = 20*mm
    
    c.rect(res_x, res_y, res_w, res_h)
    c.line(res_x, res_y + 10*mm, res_x + res_w, res_y + 10*mm)
    c.line(res_x + res_w/2, res_y, res_x + res_w/2, res_y + 10*mm)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(res_x + res_w/2, res_y + 13*mm, "INSPECTION RESULT")
    
    c.setFont("Helvetica", 12)
    c.drawCentredString(res_x + res_w/4, res_y + 3*mm, "PASS")
    c.drawCentredString(res_x + 3*res_w/4, res_y + 3*mm, "FAIL")

    # Nessuna spunta, come richiesto ("non è segnato")
    
    # ─── SIGN ───
    sign_w = 40*mm
    sign_x = WIDTH - MARGIN - sign_w - 10*mm
    sign_y = MARGIN + 5*mm
    
    c.setFont("Helvetica", 10)
    c.drawString(sign_x - 10*mm, sign_y, "SIGN")
    c.line(sign_x, sign_y, sign_x + sign_w, sign_y)

    c.showPage()
    c.save()
    
    return filepath
