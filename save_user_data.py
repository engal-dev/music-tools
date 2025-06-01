import sys
import shutil
from pathlib import Path

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import file_utils

ROOT_DIR = Path(__file__).parent
USERS_DIR_NAME = 'user-data'
USERS_DIR_PATH = Path(__file__).parent / USERS_DIR_NAME;

def save_user_files(username):
    """Copia i file specifici nella cartella dell'utente selezionato"""
    # Percorsi delle directory
    source_dir = ROOT_DIR
    target_dir = USERS_DIR_PATH / username

    # Verifica che la cartella utente esista
    if not target_dir.exists():
        print(f"Errore: La cartella dell'utente {username} non esiste")
        return False

    # File e cartelle da copiare
    items_to_copy = [
        '.env',
        '.cache',
        'navidrome-playlists',
        'spotify-playlists',
        'csv-playlists',
        'compare_report'
    ]

    # Copia i file e le cartelle specificati
    for item in items_to_copy:
        source_path = source_dir / item
        target_path = target_dir / item

        if not source_path.exists():
            print(f"Attenzione: {item} non esiste nella directory principale")
            continue

        try:
            if source_path.is_file():
                shutil.copy2(source_path, target_path)
            else:  # è una cartella
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(source_path, target_path)
            print(f"Copiato: {item}")
        except Exception as e:
            print(f"Errore durante la copia di {item}: {str(e)}")
            return False

    print("\nSalvataggio completato con successo!")
    return True

def main():
    user_folders = file_utils.get_folder_list(USERS_DIR_PATH)
    
    if not user_folders:
        print(f"Nessuna cartella utente trovata nella directory {USERS_DIR_NAME}")
        return

    # Mostra la lista delle cartelle utente
    print("\nCartelle utente disponibili:")
    for i, folder in enumerate(user_folders, 1):
        print(f"{i}. {folder}")

    # Chiedi all'utente di selezionare una cartella
    while True:
        try:
            choice = int(input("\nSeleziona il numero della cartella utente (0 per uscire): "))
            if choice == 0:
                print("Operazione annullata")
                return
            if 1 <= choice <= len(user_folders):
                selected_user = user_folders[choice - 1]
                break
            else:
                print("Scelta non valida. Riprova.")
        except ValueError:
            print("Inserisci un numero valido.")

    # Conferma la scelta
    print(f"\nHai selezionato: {selected_user}")
    confirm = input("Vuoi procedere con il salvataggio dei file? (s/n): ").lower()
    
    if confirm == 's':
        save_user_files(selected_user)
    else:
        print("Operazione annullata")

if __name__ == "__main__":
    main()