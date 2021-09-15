#!/usr/bin/env python

#  from app.models import User, Booking, Booking_GarderieMatin, Booking_GarderieSoir
from waitress import serve

from app import app, db  # noqa


@app.shell_context_processor
def make_shell_context():
    return {"db": db}


if __name__ == "__main__":
    serve(app)
