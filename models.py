from app import db 
import datetime

class Payment(db.Model):
    __tablename__ = 'payment'
    payment_id = db.Column(db.Integer, primary_key=True)
    treatment_id = db.Column(db.Integer, nullable=False)
    paypal_payment_id = db.Column(db.String(50), nullable=True)
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_status = db.Column(db.String(21), nullable=False, default="incompleted")
    pay_url = db.Column(db.String(150),nullable=True)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(150),nullable=False, default="sth u have to pay")
    modified_timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __init__(self, treatment_id, price, pay_url):
        self.treatment_id = treatment_id 
        self.price = price 
        self.pay_url = pay_url

    def json(self):
        dto={
            "description": self.description,
            'payment_id':self.paypal_payment_id,
            'treatment_id':self.treatment_id,
            'payment_status':self.payment_status,
            'price':self.price,
            'pay_url': self.pay_url,
            "last_update_time": '5 min',
            'payment_date':self.payment_date,
        }
        return dto