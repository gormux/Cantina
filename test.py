from app import app, db  # noq
from app.routes import CATEGORIES
import arrow

date_begin = arrow.get('20200901', "YYYYMMDD")
date_end =  arrow.get('20200903', "YYYYMMDD")

for category in ["cantine", "garderie_matin", "garderie_soir"]:
    data = {}
    booking = CATEGORIES[category].query.all()
    for db_line in booking:
        for date_str in db_line.booked.split():
            date = arrow.get(date_str, "YYYYMMDD")
            if date_begin <= date <= date_end:
                date_string = date.format("YYYY-MM-DD")
                if date_string not in data.keys():
                    data[date_string] = []
                data[date_string].append(db_line.username)

    print(category, data)