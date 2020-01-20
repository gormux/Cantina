# Cantina

## Installation

```bash
git clone https://github.com/gormux/Cantina.git
cd Cantina
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
./init-db.py
