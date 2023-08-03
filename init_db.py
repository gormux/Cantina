#!/usr/bin/env python
from flask import Flask
from app import db
from app.models import Configuration, User
from config import Config


def init_db():
    config = Config()
    admin = User(
        username="admin",
        name="Administrateur"
    )
    admin.set_password(config.ADMIN_PASSWORD)
    configurations = [
        ("num_tel", "Numéro de contact", 1),
        ("mail_contact", "Email de contact", 2),
        ("mail_cantine", "E-mail des personnes qui recoivent les réservations de cantine", 3),
        ("mail_cantine_time", "Heure d'envoi des réservations de cantine (HH:MM)", 4),
        ("mail_garderie", "E-mail des personnes qui recoivent les réservations de garderie", 5),
        ("mail_garderie_time", "Heure d'envoi des réservations de garderie (HH:MM)", 6),
        ("url_menu", "Adresse du site des menus", 7)
    ]
    db.init_app(app)
    with app.app_context():
        db.create_all()
        admin_exists = User.query.filter_by(username="admin").first()
        if not admin_exists:
            db.session.add(admin)
        for key, text, order in configurations:
            config_item = Configuration.query.filter_by(config_key=key).first()
            if not config_item:
                c = Configuration(config_key=key, config_text=text, config_order=order)
                db.session.add(c)
        db.session.commit()


app = Flask("cantina")
app.config.from_object(Config)
# db.init_app(app)

if __name__ == "__main__":
    init_db()
