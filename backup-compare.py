import os
import shutil
from datetime import datetime

def create_backup(directory_path):
    # Ottieni il percorso assoluto della cartella
    directory_path = os.path.abspath(directory_path)

    # Controlla che la cartella esista
    if not os.path.exists(directory_path):
        print(f"Errore: La cartella {directory_path} non esiste.")
        return

    # Ottieni la data e ora corrente nel formato AAAAMMDDHHMMSSS
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

    # Crea il percorso della cartella di backup
    backup_folder = os.path.join(directory_path, timestamp)

    try:
        # Crea la cartella di backup
        os.makedirs(backup_folder)

        # Itera sui file nella cartella principale
        for file_name in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file_name)

            # Controlla se è un file JSON, TXT o CSV
            if os.path.isfile(file_path) and file_name.lower().endswith((".json", ".txt", ".csv", ".log")):
                # Copia il file nella cartella di backup
                shutil.copy(file_path, backup_folder)

        print(f"Backup completato nella cartella: {backup_folder}")
    except Exception as e:
        print(f"Errore durante il backup: {e}")

if __name__ == "__main__":
    # Percorso della cartella da specificare come parametro
    folder_to_backup = "./compare_report"  # Modifica con il nome della tua cartella
    create_backup(folder_to_backup)