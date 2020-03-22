# ESD-Clinic

## How to run this thing? 

We run this microservice inside a container, the container will require a list of libraries (inside the requirements.txt) to function, and create a new table inside the localhost database (which has a schema called "payment" created!!!). 
Therefore, we recommend to use the following code to run: 

- sudo git clone https://github.com/Zhang-yiling/ESD-Clinic.git
- pip install -r requirements.txt
- python manage.py db init
- python manage.py db migrate
- python manage.py db upgrade
- python manage.py runserver

after these command, the payment microservice should be running on 0.0.0.0:3000 and ready for use.
