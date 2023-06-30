import serial
import threading
import tkinter as tk
from PIL import Image, ImageTk
import time
from tkinter import messagebox

# Valeur fixe par le constructeur Montratec
hStart = "01"
hStop = "03"
# Paramètres du port série
port = 'COM3' #Mettre le port correspondant
baudrate = 9600
parity = serial.PARITY_NONE
stopbits = serial.STOPBITS_ONE

# Initialisation de la connexion série
ser = serial.Serial(port, baudrate, parity=parity, stopbits=stopbits)

# Variables pour contrôler la lecture et la pause
reading = False
paused = False

# Couleurs pour l'affichage des trames reçues et envoyées
COLOR_RECEIVED = 'black'
COLOR_SENT = 'blue'

# Temps d'attente avant d'afficher un message d'absence de la navette (en millisecondes)
NO_DATA_TIMEOUT = 1500

# Fonction pour afficher les trames dans l'interface graphique
def display_frame(frame, color):
    frame_str = ' '.join(frame)
    output_text.insert(tk.END, frame_str + '\n', color)
    output_text.see(tk.END)

# Fonction pour afficher un message d'absence de la navette
def display_no_data_message():
    output_text.insert(tk.END, "La navette n'est pas présente.\n", 'error')
    output_text.see(tk.END)

# Fonction exécutée dans un thread pour lire les données du port série et séparer les trames
import time

verified_frame = []  # Variable globale pour stocker la trame vérifiée
prev_frame = []  # Variable pour stocker la trame précédente

def read_serial():
    global reading, paused, verified_frame, prev_frame

    frame_size = 7  # Taille de la trame en octets
    frame = []  # Liste pour stocker les octets de la trame
    timer_id = None  # ID du timer pour le message d'absence de la navette

    start_byte = '01'  # Octet de début (start)
    stop_byte = '03'  # Octet de fin (stop)
    start_time = None  # Temps de départ de la trame en cours

    while reading:
        # Lecture des données du port série
        data = ser.read(1)
        # Vérification de la présence de données
        if data:
            # Conversion de l'octet lu en format hexadécimal
            hex_data = data.hex().upper()

            if not frame:
                # Recherche de l'octet de début de trame
                if hex_data == start_byte:
                    frame.append(hex_data)
                    start_time = time.time()
            else:
                # Ajout de l'octet à la trame
                frame.append(hex_data)
                # Vérification de l'octet de fin de trame
                if hex_data == stop_byte and len(frame) == frame_size:
                    if not paused:
                        # Affichage de la trame reçue
                        display_frame(frame, COLOR_RECEIVED)
                    # Vérification de la trame
                    if verify_frame(frame):
                        # Mise à jour de verified_frame uniquement si la trame change et les conditions start et stop sont respectées
                        if frame != prev_frame:
                            verified_frame = frame
                            prev_frame = frame
                    frame = []
                    start_time = None
                elif time.time() - start_time > 0.025:
                    # Dépassement du délai de synchronisation
                    frame = []
                    start_time = None

        # Réinitialisation du timer d'absence de données
        if timer_id:
            window.after_cancel(timer_id)

        # Planification du timer pour afficher un message d'absence de la navette
        timer_id = window.after(NO_DATA_TIMEOUT, display_no_data_message)

def verify_frame(frame):
    start_byte = '01'  # Octet de début (start)
    stop_byte = '03'  # Octet de fin (stop)
    frame_size = 7  # Taille de la trame en octets

    if len(frame) != frame_size:
        return False

    if frame[0] != start_byte or frame[-1] != stop_byte:
        return False

    return True


# Fonction pour démarrer la lecture des données série
def start_reading():
    global reading, paused
    # Désactiver le bouton de démarrage et lancer la lecture des données série dans un thread séparé
    start_button.config(state=tk.DISABLED)
    reading = True
    paused = False
    threading.Thread(target=read_serial).start()

# Fonction pour mettre en pause ou reprendre la lecture des données série
def toggle_pause():
    global paused
    
    if paused:
        paused = False
        pause_button.config(text='Pause')
    else:
        paused = True
        pause_button.config(text='Reprendre')

# Fonction pour écrire des données sur le port série
def write_serial():
    # Récupération des données saisies dans l'entrée et conversion en octets
    data_str = input_entry.get().replace(' ', '')  # Suppression des espaces
    data = bytes.fromhex(data_str)
    
    # Vérification de la taille de la trame
    if len(data) != 7:
        output_text.insert(tk.END, "La taille de la trame doit être de 7 octets.\n", 'error')
        output_text.see(tk.END)
        return
    
    # Envoi des données sur le port série
    ser.write(data)
    
def write_serialAuto():
    # Récupération des données saisies dans l'entrée et conversion en octets
    data_str = generer_trame() # Suppression des espaces
    data = bytes.fromhex(data_str)
    
    # Vérification de la taille de la trame
    if len(data) != 7:
        output_text.insert(tk.END, "La taille de la trame doit être de 7 octets.\n", 'error')
        output_text.see(tk.END)
        return
    
    # Envoi des données sur le port série
    ser.write(data)

# Fonction pour fermer la connexion série et quitter l'application
def close_serial():
    global reading
    
    reading = False
    ser.close()
    window.quit()

def xor_binaire(a, b):
    if len(a) != len(b):
        raise ValueError("Les valeurs binaires doivent avoir la même longueur.")

    result = ""
    for i in range(len(a)):
        if a[i] == b[i]:
            result += "0"
        else:
            result += "1"
    return result

def binaire_vers_hexadecimal(binaire):
    decimal = int(binaire, 2)
    hexadecimal = hex(decimal)[2:].upper()
    return hexadecimal

def hexadecimal_vers_binaire(hexadecimal):
    decimal = int(hexadecimal, 16)
    binaire = bin(decimal)[2:]
    return binaire

def generer_trame():
    if avancer_btn.cget("relief") == tk.SUNKEN:
        hCommande = '33'
        hGroupe = verified_frame[1]
        hNum_navH = verified_frame[2]
        hNum_navL = verified_frame[3]

    if reculer_btn.cget("relief") == tk.SUNKEN:
        hCommande = '31'
        hGroupe = verified_frame[1]
        hNum_navH = verified_frame[2]
        hNum_navL = verified_frame[3]

    if changer_btn.cget("relief") == tk.SUNKEN:
        hCommande = '35'
        hGroupe = entry_groupe.get()
        hNum_navH = entry_num_navH.get()
        hNum_navL = entry_num_navL.get()

        
    bGroupe = hexadecimal_vers_binaire(hGroupe)
    bNum_navH = hexadecimal_vers_binaire(hNum_navH)
    bNum_navL = hexadecimal_vers_binaire(hNum_navL)
    bCommande = hexadecimal_vers_binaire(hCommande)

    # Pour que les binaires aient le même nombre de bits
    bGroupe = bGroupe.zfill(8)
    bNum_navH = bNum_navH.zfill(8)
    bNum_navL = bNum_navL.zfill(8)
    bCommande = bCommande.zfill(8)

    # Calcul du CheckSum
    bCheckSum = xor_binaire(bGroupe, bNum_navH)
    bCheckSum = xor_binaire(bCheckSum, bNum_navL)
    bCheckSum = xor_binaire(bCheckSum, bCommande)

    # Conversion en hexadécimal du CheckSum
    hCheckSum = binaire_vers_hexadecimal(bCheckSum)

    #Mise en forme de la trame
    trame = f"{hStart} {hGroupe} {hNum_navH} {hNum_navL} {hCommande} {hCheckSum} {hStop}"
    return trame

# Création de la fenêtre principale
window = tk.Tk()
#window.minsize(350,650)
#window.maxsize(350,650)
window.title('Communication RS232')

# Chargement de l'image
image_path = 'Projet\mfja-toulouse.ico'  # Spécifiez le chemin d'accès à votre image
image = Image.open(image_path)
image = image.resize((200, 150))  # Redimensionnement de l'image si nécessaire
photo = ImageTk.PhotoImage(image)

# Création d'un widget Label pour afficher l'image
image_label = tk.Label(window, image=photo,bg='#6BBAB9')
image_label.pack(anchor=tk.NE, padx=10, pady=10)

# Centrer l'image horizontalement et verticalement
image_label.pack(anchor=tk.CENTER)
# Créer la séparation :

# Créer les étiquettes et champs de saisie
label_groupe = tk.Label(window, text="Groupe de la navette (hexadécimal) :",bg='#6BBAB9')
entry_groupe = tk.Entry(window)

label_num_navH = tk.Label(window, text="Numéro High de la navette (hexadécimal) :",bg='#6BBAB9')
entry_num_navH = tk.Entry(window)

label_num_navL = tk.Label(window, text="Numéro Low de la navette (hexadécimal) :",bg='#6BBAB9')
entry_num_navL = tk.Entry(window)



# Création de la zone de texte pour afficher les trames
output_text = tk.Text(window, height=10, width=40)
output_text.pack()

# Création de la balise de texte pour les trames reçues
output_text.tag_config(COLOR_RECEIVED, foreground=COLOR_RECEIVED)

# Création de la balise de texte pour les trames envoyées
output_text.tag_config(COLOR_SENT, foreground=COLOR_SENT)

# Entrée pour saisir les données à envoyer sur le port série
input_entry = tk.Entry(window, width=40)
input_entry.pack()

# Création des boutons dans un cadre
button_frame = tk.Frame(window,bg='#6BBAB9')
button_frame.pack()

# Bouton pour démarrer/arrêter la lecture des données série
start_button = tk.Button(button_frame, text='Démarrer', command=start_reading)


# Bouton pour mettre en pause/reprendre la lecture des données série
pause_button = tk.Button(button_frame, text='Pause', command=toggle_pause)


# Bouton pour écrire les données saisies sur le port série
write_button = tk.Button(button_frame, text='Envoyer', command=write_serial)


# Bouton pour arrêter la lecture et fermer la connexion série
stop_button = tk.Button(button_frame, text='Arrêter', command=close_serial)

def update_buttons(active_button):
    # Désactive tous les boutons sauf le bouton actif
    if active_button != avancer_btn:
        show_entries()
        avancer_btn.config(relief=tk.RAISED)
    if active_button != reculer_btn:
        show_entries()
        reculer_btn.config(relief=tk.RAISED)
    if active_button != changer_btn:
        hide_entries()
        
        changer_btn.config(relief=tk.RAISED)
    return False
    
def avancer():
    if avancer_btn.cget("relief") == tk.SUNKEN:
        generer_trame()
        write_serialAuto()
        return update_buttons(avancer_btn)
    else:
        update_buttons(avancer_btn)
        avancer_btn.config(relief=tk.SUNKEN)
        return True
    
def reculer():
    if reculer_btn.cget("relief") == tk.SUNKEN:
        generer_trame()
        write_serialAuto()
        return update_buttons(reculer_btn)
    else:
        update_buttons(reculer_btn)
        reculer_btn.config(relief=tk.SUNKEN)
        return True

def changer():
    if changer_btn.cget("relief") == tk.SUNKEN:
        generer_trame()
        write_serialAuto()
        messagebox.showinfo("Changement",f"Le numéro de navette a été changé")
        return update_buttons(changer_btn)
        
    else:
        update_buttons(changer_btn)
        changer_btn.config(relief=tk.SUNKEN)
        return True

def hide_entries():
    label_groupe.pack_forget()
    entry_groupe.pack_forget()
    label_num_navH.pack_forget()
    entry_num_navH.pack_forget()
    label_num_navL.pack_forget()
    entry_num_navL.pack_forget()


def show_entries():
    label_groupe.pack()
    entry_groupe.pack()
    label_num_navH.pack()
    entry_num_navH.pack()
    label_num_navL.pack()
    entry_num_navL.pack()



# Création des éléments de l'interface
label_groupe = tk.Label(window, text="Groupe :",bg='#6BBAB9')
entry_groupe = tk.Entry(window)

label_num_navH = tk.Label(window, text="Numéro de navigation haut :",bg='#6BBAB9')
entry_num_navH = tk.Entry(window)

label_num_navL = tk.Label(window, text="Numéro de navigation bas :",bg='#6BBAB9')
entry_num_navL = tk.Entry(window)

Commande = tk.Label(window, text="Choix de commande:",bg='#6BBAB9')
Commande.pack()

button_frame2 = tk.Frame(window)
button_frame2.pack()

avancer_btn = tk.Button(button_frame2, text="Avancer", command=avancer)
reculer_btn = tk.Button(button_frame2, text="Reculer", command=reculer)
changer_btn = tk.Button(button_frame2, text="Changer", command=changer)

# Positionner les éléments dans la fenêtre
start_button.pack(side=tk.LEFT)
pause_button.pack(side=tk.LEFT)
write_button.pack(side=tk.LEFT)
stop_button.pack(side=tk.LEFT)

avancer_btn.pack(side=tk.LEFT)
reculer_btn.pack(side=tk.LEFT)
changer_btn.pack(side=tk.LEFT)


# Lancement de la boucle principale de l'interface graphique
window.iconbitmap("Projet\mfja-toulouse.ico")
window.config(background='#6BBAB9')
window.mainloop()

