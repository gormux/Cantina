#!/usr/bin/env python
from app import db
from app.models import User, Configuration
from config import Config

config = Config()
admin = User()
admin.set_password(config.ADMIN_PASSWORD)
admin.username = 'admin'
admin.name = 'Administrateur'
db.session.add(admin)
db.session.commit()

c = Configuration()
c.config_key = 'num_tel'
c.config_text = 'Numéro de contact'
c.config_order = 1
db.session.add(c)

c = Configuration()
c.config_key = 'mail_contact'
c.config_text = 'Email de contact'
c.config_order = 2
db.session.add(c)

c = Configuration()
c.config_key = 'mail_cantine'
c.config_text = 'E-mail des personnes qui recoivent les réservations de cantine'
c.config_order = 3
db.session.add(c)

c = Configuration()
c.config_key = 'mail_cantine_time'
c.config_text = "Heure d'envoi des réservations de cantine (HH:MM)"
c.config_order = 4
db.session.add(c)

c = Configuration()
c.config_key = 'mail_garderie'
c.config_text = 'E-mail des personnes qui recoivent les réservations de garderie'
c.config_order = 5
db.session.add(c)

c = Configuration()
c.config_key = 'mail_garderie_time'
c.config_text = "Heure d'envoi des réservations de garderie (HH:MM)"
c.config_order = 6
db.session.add(c)

c = Configuration()
c.config_key = 'url_menu'
c.config_text = "Adresse du site des menus"
c.config_order = 7
db.session.add(c)

db.session.commit()
