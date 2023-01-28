venv/bin/activate:
	py -m venv venv
	. venv/bin/activate; pip install -r requirements.txt

run: venv/bin/activate
	. venv/bin/activate; flask shell ; from app import db ; db.create_all()
