# Online-магазин

If you want to make a virtual environment:
```
For Linux:
virtualenv env
source env/bin/activate

For Windows:
py -m venv env
env\scripts\activate
```

Install dependencies:
```
For Linux and Windows:
pip install -r requirements.txt
```

Execute:
```
For Linux:
export FLASK_APP=app.py
export FLASK_ENV=development
flask run

For Windows:
set FLASK_APP=app.py
set FLASK_ENV=development
flask run
```
