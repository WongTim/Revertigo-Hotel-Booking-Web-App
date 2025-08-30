from flask import Flask, render_template, request
import sqlite3
from datetime import date, datetime
from sqlite3 import Error



app = Flask(__name__)



'''=============================== DB FUNCTIONS ============================'''


#Chooses a table and inserts following entry
def InsertEntry(table,entry):
    db = sqlite3.connect('revertigo.db')
    c = db.cursor()
    query = ''
    if table == "customers":
        query = '''INSERT INTO customers (id,name,hp,email)
                   VALUES(?,?,?,?)'''
    elif table == "booking":
        query = '''INSERT INTO booking (customer_id,room_id,check_in,check_out,total_price)
                    VALUES(?,?,?,?,?)'''
    elif table == "room":
        query = '''INSERT INTO room (room_id,room_type)
                    VALUES(?,?)'''
    elif table == "feedback":
        query = '''INSERT INTO feedback (name,email,feedback)
                    VALUES(?,?,?)'''
    else:
        return "Table not found"
    try:
        c.execute(query,entry)
    except Error as e:
        print(e)
    db.commit()
    db.close()
    return



#Pulls all data from a table
def GetAll(table):
    return sqlite3.connect("revertigo.db").cursor().execute('''SELECT * FROM ''' + str(table)).fetchall()



#Checks whether login input exists in db
def VerifyLogin(username, password):
    c = sqlite3.connect("revertigo.db").cursor()
    query = '''SELECT * FROM admin WHERE username=:username AND
                password=:password'''
    mapping = {"username":username,"password":password}
    return len(c.execute(query,mapping).fetchall()) == 1



'''===================== HELPER FUNCTIONS ===================='''

#Converts date to yyyy-mm-dd
def ConvertDate(string):
    return datetime.strptime(string, '%Y-%m-%d').date()



#Gets duration of stay in days to use in price calculation
#Duration is inclusive of start and end dates, hence the +1
def StayDuration(start,end):
    return (end-start).days + 1



'''===================== GLOBAL VARIABLES ==================='''



#Stores the info of every booking
customer_data = []
booking_data = []
room_data = []




#Cost when booking, adults children and room are all added up
final_cost = 0


#Customer data
customer_id = 1


#Room data
room_id = 0
price = 200
room_type = 'Double'





'''======================== MAIN ROUTES ======================='''


#Homepage
@app.route('/', methods=["GET"])  
def home():
    return render_template("home.html")

#Food page
@app.route('/food', methods=["GET"])
def food():
    return render_template("food.html")


#Displays the list of rooms
@app.route('/rooms', methods=["GET"])
def rooms():
    return render_template("rooms.html")



#Log in page for admin
@app.route('/login',methods=["GET"])
def login():
    return render_template("login.html")


#Log into the admin page
@app.route('/admin',methods=["POST"])
def admin():
    msg = "Incorrect username or password!"
    username = ''.join(str(request.form["username"]).split(' '))
    password = ''.join(str(request.form["password"]).split(' '))

    #If user has correct name and password
    if VerifyLogin(username,password):
        rooms = GetAll('room')
        return render_template("admin.html",rooms=rooms)
    return render_template("login.html",msg=msg)



#Takes the table name selected and redirects user
@app.route('/view_table',methods=["POST"])
def view_table():
    table = request.form["tables"]
    if table == "customer":
        customers = GetAll('customers')
        return render_template("customer_table.html",customers=customers)
    elif table=="room":
        rooms = GetAll('room')
        return render_template("room_table.html",rooms=rooms)
    elif table=="booking":
        bookings = GetAll('booking')
        return render_template('booking_table.html',bookings=bookings)
    elif table=="feedback":
        feedback =GetAll("feedback")
        return render_template('feedback_table.html',feedback=feedback)



#Contact us page
@app.route('/contact_us', methods=["GET"])
def contact():
    return render_template("contact.html")




#When user sends their contact form
@app.route('/contacted',methods=["POST"])
def contact_us():
    name = request.form["name"]
    email = request.form["email"]
    feedback = request.form["feedback"]
    feedback_data = [name,email,feedback]
    email_valid = None
    if "@" in email:
        email_valid = True
        InsertEntry("feedback",feedback_data)
    else:
        email_valid = False
    return render_template("contact.html",email_valid=email_valid)





#Called upon when the book room button is pressed
@app.route('/booking', methods=["POST"])
def booking():
    global room_id
    button_value = request.form["button"]
    room_id = button_value
    return render_template("booking.html")





#Customer input info from booking page
@app.route('/process_request',methods=["POST"])
def process_request():
    global customer_data,room_data,booking_data
    global final_cost,room_id,price,room_type,customer_id
    warning1 = "Check in date cannot be before today!"
    warning2 = "Check out date cannot be before check in!"

    #The data as input by user
    fname = request.form["f_name"].upper()
    lname = request.form["l_name"].upper()
    hp = request.form["hp"]
    email = request.form["email"]
    date_in = ConvertDate(request.form["check_in"])
    date_out = ConvertDate(request.form["check_out"])
    adults = request.form["adults"]
    children = request.form["children"]
    if int(children) == 0:
        children = 1

    #Calculations
    name = fname + ' ' + lname
    days = StayDuration(date_in,date_out)


    #User inputs start date before today's date
    if StayDuration(date.today(),date_in) < 1:
        return render_template("booking.html",warning1=warning1)

    #User inputs end date before the start date
    if days < 1:
        return render_template("booking.html",warning2=warning2)
    
    final_cost = str(round(price*int(adults)*1.5*int(children)*days,2)) + '0'

    #Store the data
    customer_data = [customer_id,name,hp,email]
    room_data = [room_id,room_type]
    booking_data = [customer_id,room_id,date_in,date_out,final_cost]

    return render_template('payment.html',final_cost=final_cost)
    


#Processes the user's payment input
@app.route('/success',methods=["POST"])
def payment():
    global customer_data,room_data,booking_data
    global customer_id
    
    #Input values
    card_no = ''.join(str(request.form["card_no"]).split(' '))
    name = request.form["name"].upper()
    cvv = request.form["cvv"]
    expiry = request.form["expiry"]

    #Insert the data when payment is done
    InsertEntry("customers",customer_data)
    InsertEntry("room",room_data)
    InsertEntry("booking",booking_data)

    #Increment the customer id
    customer_id += 1

    #Get today's date as transaction date
    today = date.today()
    
    return render_template("success.html",customer=customer_data,booking=booking_data,\
                           today=today)



app.run(debug=True, port=5078)


