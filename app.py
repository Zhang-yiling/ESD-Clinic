from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from os import environ
import json

import pika

import paypalrestsdk
import logging

app=Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://clinic_db_user:rootroot@localhost:3308/payment'
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print(app.config['SQLALCHEMY_DATABASE_URI'])

db = SQLAlchemy(app)
CORS(app)

from models import Payment

paypalrestsdk.configure(
    {
        ## merchant
        "mode": "sandbox", # sandbox or live
        "client_id": "ARiPc1IIjlwxqkCAFyBsMf8T5Z6YsxjDmU_IEmHiS8kPYw_hBt5PhzDlDqyHhI5DoYlxSWvZkWyQrLBI",
        "client_secret": "EF8H6qOQ0ZxCU3BlpuJj8roZyUDalYjtsaB6EMC1rFNZ3drIYhNTRPW4kzFP5p8Q7Hb_eFgKupVNSERq" 
    }
)

@app.route("/api/payment/all", methods=['GET'])
def get_all():
    """ Get all payment when called, usually not called """
    sorted_list = sorted(
        [payment.json() for payment in Payment.query.all()], 
        key = lambda i: i['treatment_id'],
        reverse=True
    )
    return {'payments': sorted_list}


@app.route("/api/payment/paymemt_id")
def find_payment_by_id(payment_id):
    """ search a payment detail using the payment_id """
    payment = Payment.query.filter_by(payment_id = payment_id).first()
    if payment:
        return payment.json()
    return jsonify({"message": "Payment not found."}), 404


#generate order(implementing paypal API)
# @app.route("/payment/paypalmagic/<string:payment_id>", methods=['POST'])
@app.route("/api/payment/paypalmagic", methods=['POST'])
def create_payment():
    """ create a payment in PayPal SaaS after then create it in our database """
    step_count = 0
    try:
        print("step {step}: processing new payment".format(step = step_count))
        print("------------------------------------------------------------------")
        # 1 retrieve information  about payment and payment items from the request
        step_count += 1
        try: 
            treatment_id = request.json['treatment_id']
            price = request.json['price']
            status = 201
            result = {}
            print("step {step}: get payment data: treatment_id => {t_id}, price => {price}".format(step = step_count, t_id = treatment_id, price = price))
            
        except Exception as e:
            result = {
                'status': 400, 
                "message": "An error occurred when retrieving 'treatment_id' and 'price' from request", 
                "error": str(e)
            }
            print("Error: An error occured in step {step}".format(step = step_count))
            print("------------------------------------------------------------------")
            return (result)
        
        
        # 2 check if current payment is already in the database
        step_count += 1
        print("step {step}: check if the payment_id already exist in the database".format(step = step_count))
        curr_payment = Payment.query.filter_by(treatment_id = treatment_id).first()
        if curr_payment: 
            result = {
                'status': 400, 
                "message": "This treatment_id:({0}) already in database".format(treatment_id), 
                "error": "This treatment_id:({0}) already in database".format(treatment_id)
            }
            print("An error occured in step {step}".format(step = step_count))
            return (result)
        # 3 Creating PayPal Payment Obj    
        step_count += 1
        try:
            print("step {step}: create new PayPal Obj".format(step = step_count))
            
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": "http://ec2-3-94-5-154.compute-1.amazonaws.com:80/api/payment/execute/{}".format(treatment_id),
                    "cancel_url": "http://ec2-3-94-5-154.compute-1.amazonaws.com:80/"},
                "transactions": [{
                    "item_list": {
                        "items": [{
                            # "treatment": treatment_id,
                            "name": str(treatment_id),
                            "sku": "item",
                            "price": price,
                            "currency": "SGD",
                            "quantity": 1}]},
                    "amount": {
                        "total": price,
                        "currency": "SGD"},
                    "description": "This is the payment transaction description."}]})

            print("Obj created:")
            print(payment)
            print("------------------------------------------------------------------")
        except Exception as e:
            result = {
                'status':500, 
                "message":"Can not create PayPal payment Obj, please see error for detail", 
                "error":str(e)
            }
            print("Error: An error occured in step {step}".format(step = step_count))
            return (result)

        # 4 Update new payment to database 
        step_count += 1

        if payment.create():
            print("Payment created successfully")
            print("------------------------------------------------------------------")
            try:
                print("step {step}: processing new payment".format(step = step_count))
                #authorize the payment
                for link in payment.links:
                    if link.rel=='approval_url':
                    # Convert to str to avoid google appengine unicode issue
                    # https://github.com/paypal/rest-api-sdk-python/pull/58
                        approval_url = str(link.href)
                        print("------------------------------------------------------------------")
                        print("- Treatment: {1} linked to redirect url for approval: {0}".format(approval_url, treatment_id))
                        print("------------------------------------------------------------------")
                        # Creating Payment for DB insertion 
                        print("Creating payment record in the DB")
                        print("------------------------------------------------------------------")
                        curr_payment = Payment(treatment_id = treatment_id, price = price, pay_url = approval_url)
                        print("Record created")
                        print("------------------------------------------------------------------")
                        db.session.add(curr_payment)
                        # Insert payment record into DB
                        db.session.commit()
                        print("Record added into DB")
                        print("------------------------------------------------------------------")
                status=200
                message="Payment:(linked with treatment:{0}) has been created".format(treatment_id)
                result={
                    'status': status,
                    "message":message,
                    'error': ''
                }
            except Exception as e:
                status=500
        else:
            print("Error: An error occured in step {step}:".format(step = step_count))
            print(payment.error)
            print("------------------------------------------------------------------")
            result = {
                'status':500, 
                "message":"An error occurred when creating PayPal Payment Obj", 
                "error":str(payment.error)
            }
        return result
    except Exception as e: 
        status = 500
        result={
            'status':500,
            "message":str(e)
        }
        print("Error: An error occured in step {step}".format(step = step_count))
        print("------------------------------------------------------------------")
        return result


@app.route('/api/payment/execute/<int:treatment_id>', methods = ['POST', 'GET'])
def payment_execute(treatment_id):
    """ use payment_id and payer_id to check if the payment is finished,
        if finished: use update_payment_status() to update into our db """
    # print("Executing payment_execute with payment_id: {0};".format(payment_id))
    print("Processing payment execution for treatment: {0}".format(treatment_id))
    print("------------------------------------------------------------------")
    #find a payment
    try:    
        payment_id = request.args.get('paymentId')
        token = request.args.get('token')
        payer_id = request.args.get('PayerID')
        print("get attributes")
        print("------------------------------------------------------------------")
        # get payment from PayPal
        payment = paypalrestsdk.Payment.find(payment_id)

        if payment.execute({"payer_id":payer_id}):
            # received money 
            result={'status':200,"message":"Payment execute successfully"}
            print("try update into db")
            print("------------------------------------------------------------------")
            curr_payment = update_payment_db(treatment_id, payment_id, 'complete', payer_id, token)
            print("payment for treatment: {0} updated".format(treatment_id))
            print("------------------------------------------------------------------")
        else:
            # got some error
            print("got some error in payment.execute")
            print("------------------------------------------------------------------")
            print(payment.error) # Error Hash
            result={'status':500,"message":payment.error}
        
        return redirect("http://localhost:4200/make-payment", code=302)
        # return redirect("http://localhost:4200/make-payment", code=302, Response = result)
    except Exception as e: 
        status = 500
        result={'status':500,"message":str(e)}
        print("got some error but donno what is that?????")
        print("------------------------------------------------------------------")
        return redirect("http://localhost:4200/make-payment", code=302)
        # return redirect("http://localhost:4200/make-payment", code=302, Response = result)

def update_payment_db(treatment_id, payment_id, payment_status, payer_id, token):
    """ update a payment """
    try:
        print("update payment info into db")
        print("------------------------------------------------------------------")
        paymentpaypal = paypalrestsdk.Payment.find(payment_id)
        print(paymentpaypal)
        print("------------------------------------------------------------------")

        date = paymentpaypal["update_time"]
        payment_date = paymentpaypal.transactions[0].related_resources[0].sale.update_time

        # get target payment from local DB
        curr_payment = Payment.query.filter_by(treatment_id=treatment_id).first() 
        print("get payment record: {0}".format(curr_payment.json()))
        print("------------------------------------------------------------------")
        
        curr_payment.paypal_payment_id = payment_id
        curr_payment.payment_status = payment_status
        curr_payment.payment_date = payment_date
        # commit change
        db.session.commit()
        print("record updated")
        print("------------------------------------------------------------------")
    except Exception as e: 
        print("error happened during update_payment_db()")
        print(str(e))
        print("------------------------------------------------------------------")
    return curr_payment.json()

@app.route('/api/payment/<int:payment_id>',methods=['PUT'])
def update_payment_status(payment_id):
    """ update payment """
    # get payment detail from PayPal
    paymentpaypal = paypalrestsdk.Payment.find(payment_id)
    if "state" in paymentpaypal == 'Completed':
        # update payment detail 

        # get payment from database 
        curr_payment = Payment.query.filter_by(payment_id=payment_id).first() 
        date = paymentpaypal["update_time"]
        payment_date = paymentpaypal.transactions[0].related_resources[0].sale.update_time
        payment_status = 'Completed'

        db.session.commit()
    return jsonify(payment.serialize())


# def generate_invoice(payment_id):
#     payment=Payment.query.filter_by(payment_id=payment_id)
#     paymentpaypal = paypalrestsdk.Payment.find(payment_id)
#     invoice = Invoice({
#     'merchant_info': {
#         "email": "default@merchant.com",
#     },
#     "billing_info": [{
#         "email": "example@example.com"
#     }],
#     "items": [{
#         "name": "Widgets",
#         "quantity": 20,
#         "unit_price": {
#             "currency": "USD",
#             "value": 2
#         }
#         }],
#     })

# if Invoice.create():
#     print(json.dumps(Invoice.to_dict(), sort_keys=False, indent=4))
# else:
#     print(Invoice.error)
 
if __name__ == '__main__': 
    app.run(host='0.0.0.0', port=3000, debug=True)