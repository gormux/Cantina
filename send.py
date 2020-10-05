from app.routes import CATEGORIES
import arrow
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Dictionnaire des données
data = {}


def get_data():
    # Récupération des données
    for category in ["cantine", "garderie_matin", "garderie_soir"]:
        data[category] = {}
        booking = CATEGORIES[category].query.all()
        for db_line in booking:
            for date_str in db_line.booked.split():
                date = arrow.get(date_str, "YYYYMMDD")
                date_string = date.format("YYYY-MM-DD")
                if date_string not in data[category].keys():
                    data[category][date_string] = []
                data[category][date_string].append(db_line.username)


def create_message():
    global next_week
    global today
    if sys.argv[1] in ["cantine", "cantine_api"]:
        # envoi des résultats pour la semaine suivante
        next_week = arrow.now().shift(weeks=1).week

        # Préparation du contenu des mails
        msg = f"Liste des élèves présents à la cantine pour la semaine {next_week} :\n\n"
        msg_api = (
            f"Bonjour,\n\nVoici la commande des repas pour la semaine {next_week} :\n\n"
        )

        # Pour chaque jour correspondant bien à la semaine suivante
        for day in data["cantine"]:
            if arrow.get(day, "YYYY-MM-DD").week == next_week:
                msg += f"{day} :\n"
                for p in data["cantine"][day]:
                    msg += f"- {p}\n"
                total = len(data["cantine"][day])
                msg += f"Total : {total}\n\n"
                msg_api += f"{day} : {total}\n"
        msg_api += "\nCordialement,\nSIVU des deux vallées"

    if sys.argv[1] == "garderie":
        # envoi des résultats pour la journée courante
        today = arrow.now().format("YYYY-MM-DD")
        msg = f"Liste des élèves étant prévus à la garderie le {today}:\n"
        if today in data["garderie_matin"]:
            msg += "\n- Le matin :\n"
            msg += "\n".join([u for u in data["garderie_matin"][today]])
            msg += "\n"
        if today in data["garderie_soir"]:
            msg += "\n- Le soir :\n"
            msg += "\n".join([u for u in data["garderie_soir"][today]])
            msg += "\n"

    if sys.argv[1] == "cantine_api":
        return msg_api
    else:
        return msg


if __name__ == "__main__":
    get_data()
    mail_content = create_message()
    message = MIMEMultipart()
    msg_from = "cantine@sivu-2vallees.fr"
    msg_to = "cantine@sivu-2vallees.fr"
    message.attach(MIMEText(mail_content, 'plain'))
    if sys.argv[1] == "cantine_api":
        message["Subject"] = "Réservations de repas pour le RPI des deux vallées"
    elif sys.argv[1] == "cantine":
        message["Subject"] = f"Réservations de cantine pour la semaine {next_week}"
    elif sys.argv[1] == "garderie":
        message["Subject"] = f"Réservations de garderie pour la journée du {today}"

    server = smtplib.SMTP("localhost")
    server.sendmail(msg_from, msg_to, message.as_string())
