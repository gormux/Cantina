#!/bin/bash
[ -f cantina.sqlite ] && rm -f cantina.sqlite

flask db upgrade
python init_db.py