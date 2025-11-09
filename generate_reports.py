import pandas as pd
import sys
import os
from datetime import datetime
import html  # Per html.escape()

# Importiamo i componenti di ReportLab
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
except ImportError:
    print("Errore: La libreria 'reportlab' non è installata.")
    print("Per favore, assicurati di essere nell'ambiente virtuale (venv)")
    print("e di averla installata con: pip install reportlab pandas")
    sys.exit(1)

# ==========================================================
#  IMPOSTAZIONI
# ==========================================================
# Colonna per il nome dello studente (e nome file PDF)
COLONNA_NOME_STUDENTE = "Nome e Cognome"

# Prefissi delle colonne che lo script cercherà
PREFISSO_POINTS = "Points - "
PREFISSO_CALCOLO = "CALCOLO - " # <-- Importante!

# Nome della cartella di output
OUTPUT_FOLDER = "Report_PDF_Studenti"
# ==========================================================


def pulisci_nome_file(nome):
    """
    Rimuove caratteri non validi dai nomi dei file.
    """
    return nome.replace("/", "_").replace("\\", "_").replace(":", "_").replace("?", "").replace("*", "")

def crea_pdf_studente(percorso_pdf, dati_studente, triplette_domande, stili):
    """
    Crea un singolo file PDF per uno studente.
    """
    doc = SimpleDocTemplate(percorso_pdf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []
    
    # --- 1. Titolo del Report ---
    nome_studente = dati_studente.get(COLONNA_NOME_STUDENTE, "Studente Sconosciuto")
    story.append(Paragraph(f"Report Test: {html.escape(nome_studente)}", stili['h1']))
    story.append(Paragraph(f"Data report: {datetime.now().strftime('%d/%m/%Y %H:%M')}", stili['BodyText']))
    
    # --- 2. Dati Riepilogo (Punteggio Finale e Voto) ---
    if "Punteggio_Finale_Corretto" in dati_studente:
        story.append(Spacer(1, 1 * cm))
        punti = dati_studente['Punteggio_Finale_Corretto']
        voto = dati_studente.get('Voto_su_10', 'N/D') # .get() per sicurezza
        story.append(Paragraph(f"<b>Punteggio Finale (con penalità):</b> {punti}", stili['BodyText']))
        story.append(Paragraph(f"<b>Voto Finale (su 10):</b> {voto}", stili['BodyText']))

    story.append(Spacer(1, 1.5 * cm))

    # --- 3. Lista Domande, Risposte e PUNTEGGIO CALCOLATO ---
    for (col_domanda, col_calcolo) in triplette_domande:
        
        # Prendiamo i dati dalla riga (dati_studente è una Series)
        testo_domanda = col_domanda
        risposta_data = dati_studente.get(col_domanda)
        punti_calcolati = dati_studente.get(col_calcolo) # <-- Prendiamo il punteggio calcolato

        # Formattiamo la risposta se è vuota
        if pd.isna(risposta_data) or risposta_data == '':
            testo_risposta = "<i>(Nessuna risposta data)</i>"
        else:
            testo_risposta = html.escape(str(risposta_data))

        # --- Logica Punteggio/Errore ---
        # Decidiamo cosa scrivere e con quale stile
        if punti_calcolati == 1:
            testo_punteggio = f"<b>Punteggio: 1 (CORRETTO)</b>"
            stile_punteggio = stili['PunteggioCorretto']
        elif punti_calcolati == -0.25:
            testo_punteggio = f"<b>Punteggio: -0.25 (ERRORE)</b>"
            stile_punteggio = stili['PunteggioErrore']
        elif punti_calcolati == 0:
            testo_punteggio = f"<b>Punteggio: 0 (VUOTA)</b>"
            stile_punteggio = stili['PunteggioVuoto']
        else:
            # Fallback, non dovrebbe succedere
            testo_punteggio = f"Punti: {punti_calcolati}"
            stile_punteggio = stili['BodyText']

        # Aggiungiamo gli elementi al PDF
        story.append(Paragraph(html.escape(testo_domanda), stili['h3'])) # Domanda
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(f"<b>Risposta:</b> {testo_risposta}", stili['BodyText'])) # Risposta
        story.append(Paragraph(testo_punteggio, stile_punteggio)) # Punteggio calcolato
        story.append(Spacer(1, 0.8 * cm)) # Spazio tra una domanda e l'altra

    # Costruisci il PDF
    try:
        doc.build(story)
        print(f"  > OK: Creato {percorso_pdf}")
    except Exception as e:
        print(f"  > ERRORE: Impossibile creare PDF per {nome_studente}. Dettagli: {e}")


def genera_report_da_csv(file_input):
    """
    Funzione principale: legge il CSV e orchestra la creazione dei PDF.
    """
    
    # --- 1. Controllo file e cartella output ---
    if not os.path.exists(file_input):
        print(f"Errore: Il file '{file_input}' non è stato trovato.")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"I PDF verranno salvati nella cartella: '{OUTPUT_FOLDER}'")

    # --- 2. Lettura CSV (con logica robusta) ---
    try:
        print(f"Leggendo il file: '{file_input}'...")
        try:
            df = pd.read_csv(file_input, sep=';', encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            print("Lettura in UTF-8 fallita. Tentativo con 'latin-1'...")
            df = pd.read_csv(file_input, sep=';', encoding='latin-1', low_memory=False)
        
        df = df.dropna(axis=1, how='all')

    except Exception as e:
        print(f"Errore durante la lettura del file: {e}")
        return

    # --- 3. Definiamo gli Stili PDF ---
    stili = getSampleStyleSheet()
    # Aggiungiamo stili personalizzati per i punteggi
    stili.add(ParagraphStyle(
        name='PunteggioCorretto',
        parent=stili['BodyText'],
        textColor=colors.green
    ))
    stili.add(ParagraphStyle(
        name='PunteggioErrore',
        parent=stili['BodyText'],
        textColor=colors.red,
        fontName='Helvetica-Bold' # Grassetto per evidenziare l'errore
    ))
    stili.add(ParagraphStyle(
        name='PunteggioVuoto',
        parent=stili['BodyText'],
        textColor=colors.grey
    ))

    # --- 4. Trova le coppie Domanda/Calcolo ---
    print("Scansione delle colonne per trovare le domande e i punteggi calcolati...")
    # Ora salviamo solo (col_domanda, col_calcolo)
    domande_da_reportare = []
    
    colonne_processate = list(df.columns)
    num_colonne = len(colonne_processate)
    i = 0
    
    while i < num_colonne:
        col_domanda = colonne_processate[i]
        
        # Costruiamo i nomi attesi delle colonne successive
        nome_atteso_points = f"{PREFISSO_POINTS}{col_domanda}"
        nome_atteso_calcolo = f"{PREFISSO_CALCOLO}{col_domanda}"
        
        # Cerchiamo la coppia (Domanda, Points) solo per trovare il blocco
        if (i + 1 < num_colonne and 
            colonne_processate[i+1] == nome_atteso_points):
            
            # Trovata la coppia (Domanda, Points).
            # Ora controlliamo se esiste la colonna CALCOLO corrispondente
            if nome_atteso_calcolo in df.columns:
                # Trovata! Salviamo la coppia (Domanda, Calcolo)
                domande_da_reportare.append((col_domanda, nome_atteso_calcolo))
            
            # Indipendentemente da tutto, saltiamo le colonne
            # Dobbiamo trovare il modo migliore per saltare...
            # Saltiamo solo la domanda e points, poi cercheremo feedback e calcolo...
            # MODO ROBUSTO:
            i += 1 # Passa alla prossima colonna (Points)
            while (i < num_colonne and 
                   (colonne_processate[i].startswith(PREFISSO_POINTS) or
                    colonne_processate[i].startswith("Feedback - ") or
                    colonne_processate[i].startswith(PREFISSO_CALCOLO))):
                i += 1 # Salta tutte le colonne correlate a questa domanda
        else:
            i += 1 # Non è una domanda, passa alla prossima colonna

    if not domande_da_reportare:
        print("\n*** ERRORE ***")
        print(f"Non sono state trovate colonne '{PREFISSO_CALCOLO}...'.")
        print("Assicurati di aver eseguito prima lo script 'calcola_voti.py'.")
        print(f"Esegui questo script sul file risultato (es. '..._completed_with_grades.csv')")
        return
        
    print(f"Trovate {len(domande_da_reportare)} domande da reportare.")

    # --- 5. Genera un PDF per ogni riga (studente) ---
    print("\nInizio generazione PDF per ogni studente...")
    
    if COLONNA_NOME_STUDENTE not in df.columns:
        print(f"Errore: La colonna '{COLONNA_NOME_STUDENTE}' non è stata trovata nel file.")
        print("Impossibile nominare i file PDF.")
        return

    for index, riga_studente in df.iterrows():
        
        nome = riga_studente[COLONNA_NOME_STUDENTE]
        if pd.isna(nome) or nome.strip() == "":
            nome = f"Studente_ID_{index}"
        
        nome_file = f"Report - {pulisci_nome_file(nome)}.pdf"
        percorso_file_pdf = os.path.join(OUTPUT_FOLDER, nome_file)
        
        print(f"Generando report per: {nome}...")
        
        # Passiamo anche gli stili
        crea_pdf_studente(percorso_file_pdf, riga_studente, domande_da_reportare, stili)

    print("\nGenerazione report completata.")

# --- Esecuzione Principale ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Errore: Devi specificare il nome del file CSV da processare.")
        print("Uso: python report.py \"nome_file_calcolato.csv\"")
        print("\n(Suggerimento: Esegui questo script sul file *dopo* aver")
        print("fatto girare lo script dei calcoli, es:")
        print("python report.py \"sicurezzaDSA_completed_with_grades.csv\")")
    else:
        file_da_processare = sys.argv[1]
        genera_report_da_csv(file_da_processare)