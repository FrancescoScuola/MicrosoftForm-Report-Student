import pandas as pd
import numpy as np
import sys
import os

# ==========================================================
#  IMPOSTAZIONI
# ==========================================================
PREFISSO_POINTS = "Points - "
PREFISSO_CALCOLO = "CALCOLO - "
NOME_COLONNA_FINALE = "Punteggio_Finale_Corretto"
NOME_COLONNA_VOTO = "Voto_su_10"
SUFFIX = "_completed_with_grades"
# ==========================================================


def calcola_punteggi_e_voti(file_input):
    """
    Script completo (CORRETTO):
    1. Pulisce il file CSV (con ;).
    2. Calcola i punteggi (1 / 0 / -0.25) con logica robusta.
    3. Somma i punteggi in 'Punteggio_Finale_Corretto'.
    4. Calcola il 'Voto_su_10'.
    """
    
    # --- 1. Controllo file e nome output ---
    if not os.path.exists(file_input):
        print(f"Errore: Il file '{file_input}' non è stato trovato.")
        return

    file_stem, file_ext = os.path.splitext(file_input)
    file_output = f"{file_stem}{SUFFIX}{file_ext}"
    
    # --- 2. Lettura e Fase 1: Pulizia Colonne Vuote ---
    try:
        print(f"Leggendo il file: '{file_input}'...")
        try:
            df = pd.read_csv(file_input, sep=';', encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            print("Lettura in UTF-8 fallita. Tentativo con 'latin-1'...")
            df = pd.read_csv(file_input, sep=';', encoding='latin-1', low_memory=False)

        print("Fase 1: Rimozione colonne completamente vuote...")
        df_pulito = df.dropna(axis=1, how='all')
        print(f"Colonne prima: {len(df.columns)}, Colonne dopo: {len(df_pulito.columns)}")

        # --- 3. Fase 2: Calcolo Punteggi ---
        print(f"Fase 2: Scansione e calcolo punteggi '{PREFISSO_CALCOLO}...'")
        
        colonne_finali_list = []      
        colonne_calcolate_list = []   
        numero_domande_trovate = 0
        
        colonne_da_processare = list(df_pulito.columns)
        num_colonne = len(colonne_da_processare)
        i = 0
        
        while i < num_colonne:
            nome_colonna_domanda = colonne_da_processare[i]
            colonna_domanda = df_pulito[nome_colonna_domanda]
            colonne_finali_list.append(colonna_domanda)
            
            nome_atteso_points = f"{PREFISSO_POINTS}{nome_colonna_domanda}"
            
            if (i + 1 < num_colonne and 
                colonne_da_processare[i+1] == nome_atteso_points):
                
                print(f"  > Processando: '{nome_colonna_domanda}'")
                
                colonna_points = df_pulito[nome_atteso_points]
                colonne_finali_list.append(colonna_points)
                
                series_risposte = colonna_domanda
                series_points_numeric = pd.to_numeric(colonna_points, errors='coerce')
                
                # ==========================================================
                #  LOGICA DI CALCOLO CORRETTA
                # ==========================================================
                
                # Definiamo le condizioni in modo MOLTO specifico
                
                # 1. VUOTA: La risposta è NaN o una stringa vuota
                cond_vuota = (series_risposte.isna()) | (series_risposte == '')
                
                # 2. GIUSTA: I punti sono 1
                cond_giusta = (series_points_numeric == 1)
                
                # 3. SBAGLIATA: La risposta NON è vuota E i punti sono 0
                cond_sbagliata = (cond_vuota == False) & (series_points_numeric == 0)

                # Applichiamo le condizioni. L'ordine è importante.
                # 1°: Se è vuota -> 0
                # 2°: Se è giusta -> 1
                # 3°: Se è sbagliata -> -0.25
                punteggio_calcolato_array = np.select(
                    [cond_vuota, cond_giusta, cond_sbagliata],  # Condizioni
                    [0, 1, -0.25],                               # Risultati
                    default=0  # Default (se non è nessuna delle 3, es. Punti=NaN)
                )
                # ==========================================================
                
                nome_colonna_calcolata = f"{PREFISSO_CALCOLO}{nome_colonna_domanda}"
                series_calcolata = pd.Series(punteggio_calcolato_array, 
                                             name=nome_colonna_calcolata, 
                                             index=df_pulito.index)
                
                colonne_finali_list.append(series_calcolata)
                colonne_calcolate_list.append(series_calcolata)
                
                numero_domande_trovate += 1
                i += 2
            
            else:
                i += 1
        
        # --- 4. Fase 3: Assemblaggio Finale, Somma e Voto ---
        print("Fase 3: Assemblaggio del DataFrame finale...")
        
        df_finale = pd.concat(colonne_finali_list, axis=1)

        if colonne_calcolate_list:
            print(f"Trovate {numero_domande_trovate} domande con punteggio.")
            
            df_somma_calcolata = pd.concat(colonne_calcolate_list, axis=1)
            df_finale[NOME_COLONNA_FINALE] = df_somma_calcolata.sum(axis=1, skipna=True)
            print(f"Aggiunta colonna di somma: '{NOME_COLONNA_FINALE}'")
            
            if numero_domande_trovate > 0:
                punteggio_massimo_possibile = numero_domande_trovate
                punteggio_per_voto = df_finale[NOME_COLONNA_FINALE].clip(lower=0)
                voto_calcolato = (punteggio_per_voto / punteggio_massimo_possibile) * 10
                
                df_finale[NOME_COLONNA_VOTO] = voto_calcolato.round(2)
                print(f"Aggiunta colonna voto: '{NOME_COLONNA_VOTO}'")
            else:
                print("Nessuna domanda trovata, impossibile calcolare il voto.")
                
        else:
            print("Attenzione: non sono state trovate colonne calcolate.")

        # --- 5. Fase 4: Salvataggio ---
        print(f"Salvataggio in corso su: '{file_output}'...")
        
        df_finale.to_csv(file_output, index=False, encoding='utf-8-sig', sep=';')
        
        print(f"\nOperazione completata! File salvato in: '{file_output}'")

    except Exception as e:
        print(f"Si è verificato un errore imprevisto: {e}")

# --- Esecuzione Principale ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Errore: Devi specificare il nome del file da processare.")
        print(f"Uso: python {sys.argv[0]} \"nome_file.csv\"")
    else:
        nome_file_da_processare = sys.argv[1]
        calcola_punteggi_e_voti(nome_file_da_processare)