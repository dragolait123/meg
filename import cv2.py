import cv2
import mediapipe as mp
import pyautogui
import speech_recognition as sr
import webbrowser
import tkinter as tk
from tkinter import Label
import threading
import pyttsx3
import os
import math
import random
import tkinter as tk
from tkinter import Entry
import pyautogui  # Importation de la bibliothèque pour simuler des frappes clavier
import cv2
import mediapipe as mp
import pygame
import numpy as np
from pynput.keyboard import Controller
import time
import subprocess
subprocess.Popen(["python", "background_task.py"])

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bienvenue sur Meg!"

if __name__ == "__main__":
    # Démarrage automatique du serveur Flask
    app.run(host="0.0.0.0", port=5000)


# Initialisation de Mediapipe pour le suivi des mains
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Initialisation de Pygame pour afficher le clavier
pygame.init()
screen_width, screen_height = 1280, 720  # Taille de l'écran
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Clavier Virtuel")

# Définition des touches du clavier
keys = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
        ["Z", "X", "C", "V", "B", "N", "M"]]

key_size = 80  # Taille des touches
key_spacing = 15
keyboard_width = (key_size + key_spacing) * 10
keyboard_height = (key_size + key_spacing) * 3
keyboard_top_left = ((screen_width - keyboard_width) // 2, (screen_height - keyboard_height) // 2)

# Contrôleur clavier
keyboard = Controller()
pressed_keys = {}
press_delay = 0.5  # Délai entre deux frappes identiques (en secondes)

def draw_keyboard():
    """Affiche le clavier centré à l'écran"""
    x, y = keyboard_top_left
    for row in keys:
        for key in row:
            rect = pygame.Rect(x, y, key_size, key_size)
            pygame.draw.rect(screen, (255, 255, 255), rect, border_radius=5)
            font = pygame.font.Font(None, 48)
            text = font.render(key, True, (0, 0, 0))
            screen.blit(text, (x + key_size // 3, y + key_size // 4))
            x += key_size + key_spacing
        x = keyboard_top_left[0]
        y += key_size + key_spacing

# Initialisation de la capture vidéo
cap = cv2.VideoCapture(0)
running = True

while running:
    success, frame = cap.read()
    if not success:
        continue
    
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    screen.fill((0, 0, 0))
    draw_keyboard()
    
    current_time = time.time()
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            for lm in hand_landmarks.landmark:
                cx, cy = int(lm.x * screen_width), int(lm.y * screen_height)
                pygame.draw.circle(screen, (0, 255, 0), (cx, cy), 15)  # Points de suivi
                
                # Vérification de la collision avec les touches
                x, y = keyboard_top_left
                for row in keys:
                    for key in row:
                        rect = pygame.Rect(x, y, key_size, key_size)
                        if rect.collidepoint(cx, cy):
                            pygame.draw.rect(screen, (0, 255, 255), rect, border_radius=5)
                            if key not in pressed_keys or (current_time - pressed_keys[key]) > press_delay:
                                pressed_keys[key] = current_time
                                keyboard.press(key)
                                keyboard.release(key)
                        x += key_size + key_spacing
                    x = keyboard_top_left[0]
                    y += key_size + key_spacing
            
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    
    cv2.imshow("Camera", frame)
    pygame.display.flip()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

cap.release()
cv2.destroyAllWindows()
pygame.quit()

# Configuration de PyAutoGUI
pyautogui.FAILSAFE = False

# Initialisation de MediaPipe pour le suivi de la main et de l'index
mp_hands = mp.solutions.hands
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Initialisation de la caméra
cap = cv2.VideoCapture(0)


# Sensibilité
SENSIBILITE = 1.0  # Ajuste cette valeur pour définir la réactivité du mouvement

# Initialisation du synthétiseur vocal
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('voice', 'french')

def parler(texte):
    engine.say(texte)
    engine.runAndWait()

# Interface Graphique
root = tk.Tk()
root.title("Meg AI - Assistant Virtuel")
root.geometry("400x300")
root.configure(bg='black')

label = Label(root, text="Meg est activée", font=("Arial", 16), fg="cyan", bg="black")
label.pack(pady=20)

# Fonction pour calculer la distance entre deux points
def calculer_distance(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

# Fonction pour détecter un pincement
def detecter_pincement(thumb, index_finger):
    distance = calculer_distance(thumb, index_finger)
    return distance < 0.05  # Ajuste cette valeur pour affiner la détection

# Variable pour compter le nombre de pincements
compteur_pincements = 0

# Mode dessin
dessiner = False
dessins = []

def dessiner_souris(position, frame):
    if dessiner:
        dessins.append(position)
        for point in dessins:
            cv2.circle(frame, (int(point[0]), int(point[1])), 5, (0, 255, 0), -1)

def detecter_balayage(p1, p2, direction="gauche-droite"):
    if direction == "gauche-droite":
        return p1.x < p2.x - 0.1
    elif direction == "haut-bas":
        return p1.y < p2.y - 0.1
    return False

# Fonction pour suivre la main et contrôler le curseur
def suivi_main():
    global compteur_pincements, dessiner

    with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
        position_precedente = None
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Récupérer la position de la main
                    thumb = hand_landmarks.landmark[4]  # Pouce (point 4)
                    index_finger = hand_landmarks.landmark[8]  # Index (point 8)

                    # Afficher la position de la main
                    cv2.putText(frame, f"Position Pouce: ({thumb.x:.2f}, {thumb.y:.2f})", 
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
                    cv2.putText(frame, f"Position Index: ({index_finger.x:.2f}, {index_finger.y:.2f})", 
                                (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                    # Déplacer le curseur de la souris
                    largeur_ecran, hauteur_ecran = pyautogui.size()
                    position_index_x = int(index_finger.x * largeur_ecran)
                    position_index_y = int(index_finger.y * hauteur_ecran)
                    pyautogui.moveTo(position_index_x, position_index_y)

                    # Vérifier si un pincement est détecté
                    if detecter_pincement(thumb, index_finger):
                        compteur_pincements += 1
                        print(f"Pincement détecté! Compteur: {compteur_pincements}")

                        # Si 3 pincements sont détectés, effectuer une sélection (clic)
                        if compteur_pincements >= 3:
                            pyautogui.click()  # Clic de souris
                            print("Sélection effectuée!")
                            compteur_pincements = 0  # Réinitialiser le compteur après la sélection

                    # Dessiner avec l'index
                    if position_precedente is not None:
                        if detecter_balayage(position_precedente, index_finger, direction="gauche-droite"):
                            # Effacer les dessins si un balayage est détecté
                            dessins.clear()
                            print("Mouvement de balayage détecté, dessins supprimés.")
                        else:
                            dessiner_souris((index_finger.x * pyautogui.size().width, index_finger.y * pyautogui.size().height), frame)

                    position_precedente = index_finger

            # Affichage de la vidéo
            cv2.imshow("Suivi de la main", frame)

            # Quitter avec la touche 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

# Commande vocale en écoute continue
def reconnaissance_vocale_continue():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        while True:
            label.config(text="Écoute...")
            audio = recognizer.listen(source)
            try:
                command = recognizer.recognize_google(audio, language='fr-FR')
                label.config(text=f"Commande: {command}")
                parler(f"Commande reçue: {command}")
                
                # Commandes vocales existantes
                if "ouvre YouTube" in command:
                    webbrowser.open("https://www.youtube.com")
                elif "ouvre Google" in command:
                    webbrowser.open("https://www.google.com")
                elif "éteins l'ordinateur" in command:
                    parler("Extinction de l'ordinateur en cours")
                    os.system("shutdown /s /t 1")
                elif "ouvre un programme" in command:
                    os.system("start notepad")  # Exemple pour ouvrir Notepad
                elif "ferme le programme" in command:
                    os.system("taskkill /im notepad.exe")
                elif "ouvre calculatrice" in command:
                    os.system("calc.exe")  # Exemple pour ouvrir la calculatrice
                    parler("Ouverture de la calculatrice")
                elif "ouvre explorateur" in command:
                    os.system("explorer")  # Exemple pour ouvrir l'explorateur
                    parler("Ouverture de l'explorateur de fichiers")
                elif "recherche" in command:
                    rechercher_sur_internet(command)
                elif "met à jour l'application" in command:
                    parler("Mise à jour de l'application en cours...")
                    mise_a_jour()
                elif "redémarre l'ordinateur" in command:
                    parler("Redémarrage de l'ordinateur en cours...")
                    os.system("shutdown /r /t 1")  # Redémarre l'ordinateur
                elif "change de mode" in command:
                    changer_mode()
                elif "affiche effet visuel" in command:
                    afficher_effet_visuel()
                elif "suivre les gestes" in command:
                    activer_suivi_gestes()
                elif "dessin activé" in command:
                    global dessiner
                    dessiner = True
                    parler("Mode dessin activé")
                elif "dessin désactivé" in command:
                    dessiner = False
                    dessins.clear()
                    parler("Mode dessin désactivé")
                elif "ouvre photoshop" in command:
                    os.system("start photoshop")  # Ouvre Photoshop
                elif "éteins la lumière" in command:
                    print("Commande envoyée à l'objet connecté")  # Ajoute ton API ici
                elif "active le mode productivité" in command:
                    os.system("start focus.exe")  # Exemple d'application de concentration
                    pyautogui.hotkey("win", "d")  # Réduit toutes les fenêtres

                # Commandes supplémentaires
                elif "minimise la fenêtre" in command:
                    pyautogui.hotkey('win', 'd')  # Minimiser la fenêtre active
                    parler("Fenêtre minimisée")
                elif "maximise la fenêtre" in command:
                    pyautogui.hotkey('win', 'up')  # Maximiser la fenêtre active
                    parler("Fenêtre maximisée")
                elif "ferme la fenêtre" in command:
                    pyautogui.hotkey('alt', 'f4')  # Fermer la fenêtre active
                    parler("Fenêtre fermée")
                elif "ouvre Facebook" in command:
                    webbrowser.open("https://www.facebook.com")
                    parler("Ouverture de Facebook")
                elif "ouvre Twitter" in command:
                    webbrowser.open("https://www.twitter.com")
                    parler("Ouverture de Twitter")
                elif "augmente le volume" in command:
                    pyautogui.press('volumeup')  # Augmenter le volume
                    parler("Volume augmenté")
                elif "diminue le volume" in command:
                    pyautogui.press('volumedown')  # Diminuer le volume
                    parler("Volume diminué")
                elif "joue de la musique" in command:
                    os.system("start wmplayer")  # Lance Windows Media Player (exemple)
                    parler("Lecture de la musique")
                elif "pause la musique" in command:
                    pyautogui.hotkey('space')  # Mettre en pause la musique ou vidéo
                    parler("Musique mise en pause")
                elif "prend une capture d'écran" in command:
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshot.png")  # Sauvegarder la capture
                    parler("Capture d'écran effectuée")
                elif "lance mon script d'automatisation" in command:
                    os.system("python my_script.py")  # Lance un script Python
                    parler("Script d'automatisation lancé")
                # Ajouter une commande vocale pour générer un QR code
                elif "génère un code QR" in command:
                    generate_qr("https://meg-assistant.com")

            except sr.UnknownValueError:
                label.config(text="Je n'ai pas compris")
            except sr.RequestError:
                label.config(text="Erreur de connexion")

# Fonction pour rechercher sur Internet
def rechercher_sur_internet(command):
    recherche = command.replace("recherche", "").strip()
    if recherche:
        url = f"https://www.google.com/search?q={recherche}"
        webbrowser.open(url)
        parler(f"Recherche de {recherche}")
    else:
        parler("Veuillez spécifier ce que vous voulez rechercher.")

# Fonction de mise à jour
def mise_a_jour():
    os.system("python update_script.py")  # Remplacer par le script réel de mise à jour

# Fonction pour changer de mode
def changer_mode():
    parler("Mode changé.")

# Fonction pour afficher un effet visuel
def afficher_effet_visuel():
    parler("Affichage d'un effet visuel.")

# Fonction pour activer le suivi des gestes
def activer_suivi_gestes():
    parler("Suivi des gestes activé.")
    threading.Thread(target=suivi_main, daemon=True).start()
# Fonction pour filtrer les positions (moyenneur pour stabiliser la position)
class Stabilisateur:
    def __init__(self, taille_fenetre=5):
        self.buffer = []
        self.taille_fenetre = taille_fenetre

    def ajouter(self, valeur):
        self.buffer.append(valeur)
        if len(self.buffer) > self.taille_fenetre:
            self.buffer.pop(0)
        return sum(self.buffer) / len(self.buffer)

def suivi_index():
    with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Récupérer la position de l'index et du pouce
                    index_finger = hand_landmarks.landmark[8]  # L'index (point 8)

                    # Appliquer le stabilisateur pour lisser les mouvements
                    x_index = int(index_finger.x * pyautogui.size().width * SENSIBILITE)
                    y_index = int(index_finger.y * pyautogui.size().height * SENSIBILITE)

                    # Stabiliser les positions
                    x_index_stabilise = stabilisateur_x.ajouter(x_index)
                    y_index_stabilise = stabilisateur_y.ajouter(y_index)

                    # Empêcher que le curseur ne sorte de l'écran
                    x_index_stabilise = max(0, min(x_index_stabilise, pyautogui.size().width - 1))
                    y_index_stabilise = max(0, min(y_index_stabilise, pyautogui.size().height - 1))

                    # Déplacer le curseur
                    pyautogui.moveTo(x_index_stabilise, y_index_stabilise)

                    # Vérifier si l'index et le pouce sont assez proches pour un clic
                    distance = calculer_distance(index_finger, hand_landmarks.landmark[4])  # Pouce (point 4)
                    if distance < 0.05:  # Si la distance est inférieure à une certaine valeur
                        pyautogui.click()  # Clic de souris
                        

            # Affichage de la vidéo
            cv2.imshow("Suivi de l'index", frame)

            # Quitter avec la touche 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


# Démarrer l'écoute des commandes vocales dans un thread séparé
threading.Thread(target=reconnaissance_vocale_continue, daemon=True).start()

root.mainloop()




