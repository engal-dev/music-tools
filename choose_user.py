import sys
import shutil
from pathlib import Path

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import file_utils

ROOT_DIR = Path(__file__).parent
USERS_DIR_NAME = 'user-data'
USERS_DIR_PATH = Path(__file__).parent / USERS_DIR_NAME;

def copy_user_files(username):
    """Copia i file e le cartelle dalla cartella dell'utente selezionato"""
    # Percorsi delle directory
    auth_dir = USERS_DIR_PATH / username
    target_dir = ROOT_DIR

    # Verifica che la cartella utente esista
    if not auth_dir.exists():
        print(f"Errore: La cartella dell'utente {username} non esiste")
        return False

    try:
        # Elimina solo i file e le cartelle che corrispondono a quelli nella cartella utente
        for item in auth_dir.glob('*'):
            target_item = target_dir / item.name
            if target_item.exists():
                if target_item.is_file():
                    target_item.unlink()
                elif target_item.is_dir():
                    shutil.rmtree(target_item)
        
        # Copia tutti i file e le cartelle dalla cartella utente alla directory target
        shutil.copytree(auth_dir, target_dir, dirs_exist_ok=True)
        print("\nCopia completata con successo!")
        return True
    except Exception as e:
        print(f"Errore durante la copia: {str(e)}")
        return False

def main():
    # Ottieni la lista delle cartelle utente
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
    confirm = input("Vuoi procedere con la copia dei file? (s/n): ").lower()
    
    if confirm == 's':
        copy_user_files(selected_user)
    else:
        print("Operazione annullata")

if __name__ == "__main__":
    main() 