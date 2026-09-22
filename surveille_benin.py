"""
Surveille https://voyage.benin.bj/ et envoie un email d'alerte
dès que la page d'attente "bientôt disponible" disparaît.

Usage :
    python surveille_benin.py          # vérification normale
    python surveille_benin.py --test   # envoie un email de test
"""
import os
import smtplib
import sys
import urllib.request
from email.message import EmailMessage

URL = "https://voyage.benin.bj/"
# Formulations présentes sur la page d'attente actuelle
MARQUEURS = [
    "bientôt disponible",
    "bient&ocirc;t disponible",
    "sera bientôt",
]

EXPEDITEUR = os.environ.get("EMAIL_EXPEDITEUR", "").strip()
MOT_DE_PASSE = os.environ.get("EMAIL_MOT_DE_PASSE", "").replace(" ", "").strip()
DESTINATAIRE = os.environ.get("EMAIL_DESTINATAIRE", "").strip() or EXPEDITEUR


def lire_page() -> str:
    req = urllib.request.Request(
        URL, headers={"User-Agent": "Mozilla/5.0 (surveillance ouverture billetterie)"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def envoyer_mail(sujet: str, corps: str) -> None:
    if not EXPEDITEUR or not MOT_DE_PASSE:
        sys.exit("Erreur : les secrets EMAIL_EXPEDITEUR et EMAIL_MOT_DE_PASSE ne sont pas configurés.")
    msg = EmailMessage()
    msg["Subject"] = sujet
    msg["From"] = EXPEDITEUR
    msg["To"] = DESTINATAIRE
    msg.set_content(corps)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as serveur:
        serveur.login(EXPEDITEUR, MOT_DE_PASSE)
        serveur.send_message(msg)


def main() -> None:
    if "--test" in sys.argv:
        envoyer_mail(
            "Test : surveillance billets Bénin",
            "Tout fonctionne. Tu recevras un email ici dès que le site voyage.benin.bj change.",
        )
        print("Email de test envoyé.")
        return

    try:
        html = lire_page().lower()
    except Exception as e:
        # Site injoignable : pas d'alerte, on réessaiera au prochain passage
        print(f"Site injoignable pour l'instant : {e}")
        return

    if any(m in html for m in MARQUEURS):
        print("Toujours en mode 'bientôt disponible'. Rien à signaler.")
        return

    envoyer_mail(
        "🛫 Billets Bénin : le site a changé !",
        "La page d'attente a disparu sur voyage.benin.bj.\n"
        "Les vols spéciaux sont peut-être en vente : va vérifier vite !\n\n"
        f"{URL}",
    )
    print("Changement détecté, email envoyé.")


if __name__ == "__main__":
    main()
