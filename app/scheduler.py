import sqlalchemy
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message

from app import app, db
from app.models import Configuration
from config import Config


def init_scheduler():
    config = Config()

    scheduler = BackgroundScheduler()
    scheduler.add_jobstore('sqlalchemy', url=config.SQLALCHEMY_SCHEDULER_DATABASE_URI)
    scheduler.start()

    try:
        app_config = {}
        for i in db.session.query(Configuration).order_by('config_order'):
            app_config[i.config_key] = {'order': i.config_order, 'text': i.config_text, 'value': i.value}
        for config in app_config:
            if config in ['mail_cantine_time', 'mail_garderie_time']:
                hour, minute = app_config[config]['value'].split(':')
                mail_list = app_config[config.replace('_time', '')]['value'].split(' ')
                args = {}
                args['mail_list'] = mail_list
                scheduler.add_job(send_mail,
                                  'cron',
                                  day_of_week='mon-fri',
                                  hour=hour,
                                  minute=minute,
                                  replace_existing=True,
                                  id=config,
                                  kwargs=args)
        print('Scheduler initialized')
        return scheduler
    except sqlalchemy.exc.OperationalError:
        return False


def send_mail(mail_list=None, book_cantine=None, book_garderie=None, day=None):
    with app.app_context():
        mail = Mail(app)
        day = day[0:4] + '/' + day[5:6] + '/' + day[7:8]
        if book_cantine:
            msg = Message(f'Réservations Cantine pour le {day}',
                          sender='julien@gormotte.info',
                          recipients=mail_list)
            text = f'Bonjour,\nVoici la liste des {len(book_cantine)} élèves inscrits à la cantine pour le {day} :'
            for pupil in book_cantine:
                text += f'\n{pupil}'
            msg.body = text
            mail.send(msg)
        if book_garderie:
            msg = Message(f'Réservations Garderie pour le {day}',
                          sender='julien@gormotte.info',
                          recipients=mail_list)
            text = f'Bonjour,\nVoici la liste des élèves inscrits à la garderie pour le {day} :'
            for period in book_garderie:
                text += f'\n{len(book_garderie[period])} élèves inscrits à la {period} :'
                for pupil in book_garderie[period]:
                    text += f'\n{pupil}'
            msg.body = text
            mail.send(msg)
