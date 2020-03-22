FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app.py app.py
COPY manage.py manage.py
COPY models.py models.py

ENV dbURL=mysql+mysqlconnector://clinic_db_user:rootroot@localhost:3306/payment

EXPOSE 3000