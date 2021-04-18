from flask import Flask, render_template, session, request, redirect, url_for, g
from database import get_db, close_db
from forms import RegistrationForm, LoginForm, PasswordForm, BookingForm, TransferForm, FriendForm, EmployeeForm, EmployeeRegistrationForm, LoanForm, EditProfilePage
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import datetime

#Configurations.
app = Flask(__name__)
app.config["SECRET_KEY"] = "[REDACTED]"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
Session(app)

"""
--------------
Author: Ciarán Cotter
Date of Completion: 26/03/2021

--------------
Important Note
--------------
While it is inevitable that certain parts of my code such as the standard login and cart will resemble others, that is because of the labs.
All other code - most notably the password reset function, friend system, bank system, event logger and employee login system
are all 100% original. Any similarities with others are likely the result of coincidence. I believe that my website is 
almost entirely bug-free at this point. I hope you enjoy browsing through the site.

----------------
Employee Account
----------------
The secret pass needed to sign up with an employee account is "[REDACTED]". The employee account has access to site logs. Employees
can also see the entire bank history. 

----------------
Standard Account
----------------
The standard user can send my project's virtual currency, Waluigi Dollars, to other users through a bank interface. 
They can take out a loan of this virtual currency as well. The user can track their transaction history with ease. 
They can also send friend requests to other users, accept friend requests from other users, and have persistent friends. 
Once they are friends, they can easily access each other's profiles. They can set their profile pictures to be different GIFs,
and customise their biographies. There are 10 different GIFs to choose from, and I have attributed them in a .txt file in the directory.
There is, of course, standard cart functionality that has been modified to display various totals. They can pay for their food using Waluigi Dollars.
The standard user can also print out a copy of their invoice that is automatically generated upon the purchase of foods from the menu, by simply
clicking a button at the checkout screen. This invoice calculates VAT tax as well, and displays the purchased items along with quantity, price,
price before tax, price after tax, tax total and overall total. 
The standard user is able to reset their password as well.

You may need to make a second account on my website to test some functionality such as adding friends and sending Waluigi Dollars between accounts.
"""

#Logs site activity, taking inputs for the user and the action itself.
def eventLogger(person, action):
    eventTime = datetime.datetime.now()
    db = get_db()
    db.execute('''INSERT INTO events(event_subject, event_action, event_time)
        VALUES(?, ?, ?)''', (person, action, eventTime))
    db.commit() 
    print("Event Logged!")

@app.teardown_appcontext
def close_db_at_end_of_requests(e=None):
    close_db(e)

@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id",None)
    g.employee = session.get("employee_id", None)
    g.balance = session.get("balance", None)

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login", next=request.url))
        return view(**kwargs)
    return wrapped_view

#Employee wrapper that limits certain pages to employee-only access.
def is_employee(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.employee is None:
            return redirect(url_for("employee_login", next=request.url))
        return view(**kwargs)
    return wrapped_view

#Default route.
@app.route("/")
def index():
    return render_template("index.html")

#Employee homepage.
@app.route("/employee_home", methods = ["GET", "POST"])
@is_employee
def employee_home():
    return render_template("employee_home.html")

#Password reset 
@app.route("/details", methods=["GET","POST"])
@login_required
def details():

    #Form for changing password
    form = PasswordForm()
    
    if form.validate_on_submit():
        currentPass = form.currentPass.data
        newPass = form.newPass.data
        newPassAgain = form.newPassAgain.data

        #Getting the current user's password
        db = get_db()
        user_id = g.user
        user = db.execute(''' SELECT * FROM users
                            WHERE user_id = ?;''',(user_id,)).fetchone()
        
        
            #Ensuring that a user_id exists
        if currentPass is None:
            form.currentPass.errors.append("Unknown user id")
            
            #Check if your new password confirmation is correct
        if not newPass == newPassAgain:
                form.newPass.errors.append("Passwords do not match.")
        
        elif not check_password_hash(user["password"], currentPass):
            form.newPass.errors.append("Your password is incorrect.")

        #SQL UPDATE statement for updating the password in the database
        else:
            db.execute('''UPDATE users
                        SET password = ?
                        WHERE user_id = ?;''',((generate_password_hash(newPass)), user_id))

            db.commit()
            form.newPassAgain.errors.append("Password updated.")    

    return render_template("details.html", form=form)

#Basic registration
@app.route("/register", methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        password2 = form.password2.data
        bio = form.bio.data
        pfp = form.pfp.data

        db = get_db()
        check = db.execute(''' SELECT * FROM users
                            WHERE user_id = ?;''',(user_id,)).fetchone()
        if check:
            form.user_id.errors.append("Username already taken!")
            return render_template("register.html", form=form)

        elif not check:
            db.execute('''INSERT INTO users (user_id,password,balance, bio, pfp)
                            VALUES (?,?,?,?,?);''', (user_id, generate_password_hash(password), 100, bio, pfp))
            db.commit()
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

#Registration for employees. Requires the Secret Pass value that I have only distributed to certain people.
@app.route("/employee_register", methods=["GET","POST"])
def employee_register():
    form = EmployeeRegistrationForm()
    if form.validate_on_submit():
        employee_id = form.employee_id.data
        password = form.password.data
        secret = form.secret.data
        db = get_db()
        check = db.execute(''' SELECT * FROM employees
                            WHERE employee_id = ?;''',(employee_id,)).fetchone()
        if check:
            form.employee_id.errors.append("Username already taken!")
            return render_template("employee_register.html", form=form)

        elif not check:
            if secret == "[REDACTED]":
                db.execute('''INSERT INTO employees (employee_id ,password)
                                VALUES (?,?);''', (employee_id, generate_password_hash(password),))
                db.commit()
            else:
                form.secret.errors.append("Secret Pass is incorrect!")
                return render_template("employee_register.html", form=form)
        return redirect(url_for("employee_login"))
    return render_template("employee_register.html", form=form)

#Login
@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()
        user = db.execute(''' SELECT * FROM users
                                WHERE user_id = ?;''',(user_id,)).fetchone()
        
        if user is None:
            form.user_id.errors.append("Unknown user id")
        elif not check_password_hash(user["password"],password):
            form.password.errors.append("Incorrect password!")
            eventLogger(user_id, "got their password wrong")
        else:
            session.clear()
            session["user_id"] = user_id
            eventLogger(user_id, "logged in")
            balance = db.execute(''' SELECT * FROM users
                        WHERE user_id = ?;''',(user_id,)).fetchone()["balance"]
            session["balance"] = balance
            
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for("index")
            return redirect(next_page)
    return render_template("login.html", form=form)

#Employee Login 
@app.route("/employee_login", methods=["GET","POST"])
def employee_login():
    form = EmployeeForm()
    if form.validate_on_submit():
        employee_id = form.employee_id.data
        password = form.password.data
        db = get_db()
        employee = db.execute(''' SELECT * FROM employees
                                WHERE employee_id = ?;''',(employee_id,)).fetchone()

        if employee is None:
            form.employee_id.errors.append("Unknown employee id")

        elif not check_password_hash(employee["password"],password):
            form.password.errors.append("Incorrect password!")
            eventLogger(employee_id, "got their password wrong")
            
        else:
            session.clear()
            session["employee_id"] = employee_id
            eventLogger(employee_id, "logged in")
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for("employee_home")
            return redirect(next_page)
    return render_template("employee_login.html", form=form)

#Log out
@app.route("/logout")
def logout():
    if g.user:
        eventLogger(g.user, "logged out")
    elif g.employee:
        eventLogger(g.employee, "logged out")
    session.clear()
    return redirect(url_for("index"))

#Basic bank system
@app.route("/bank", methods=["GET","POST"])
def bankTransfer():

    db = get_db()
    user_id = g.user
    balance = round(g.balance, 2) 
    form = TransferForm()

    if form.validate_on_submit():
        recipient = form.recipient.data
        amount = form.amount.data
        db = get_db()
        receiving = db.execute(''' SELECT * FROM users
                            WHERE user_id = ?;''',(recipient,)).fetchone()
        sender = db.execute(''' SELECT * FROM users
                            WHERE user_id = ?;''',(user_id,)).fetchone()["balance"]

        if receiving is None:
            form.recipient.errors.append("Person does not exist!")

        elif receiving is not None:   
            if recipient != user_id:
                receiver = receiving["balance"]
                receiver_name = str(receiving["user_id"])

                if balance >= amount:
                    #Enough in account
                    if amount > 0:
                        currentTransaction = datetime.datetime.now()
                        db.execute('''UPDATE users
                                    SET balance = ?
                                    WHERE user_id = ?;''',(sender - float(amount), user_id))
                        db.commit()
                        db.execute('''UPDATE users
                                    SET balance = ?
                                    WHERE user_id = ?;''', (receiver + float(amount), recipient))
                        db.commit()
                        db.execute('''INSERT INTO transactions(sender, receiver, amount, time_of_transaction)
                                    VALUES(?, ?, ?, ?);''', (user_id, receiver_name, float(amount), currentTransaction))
                        db.commit()
                        form.recipient.errors.append("Sent Waluigi Dollars successfully.")
                        eventLogger(user_id, "sent Waluigi Dollars to someone")
                        currentBal = db.execute(''' SELECT * FROM users
                                WHERE user_id = ?;''',(user_id,)).fetchone()["balance"]
                        session["balance"] = currentBal
                    else:
                        form.recipient.errors.append("Nice try...")

                else:
                    form.recipient.errors.append("Bank said no! Go get a job, loser!")  
                    eventLogger(user_id, "failed to send Waluigi Dollars")  
            else:
                form.recipient.errors.append("Can't send money to yourself...")    
                eventLogger(user_id, "tried to send themselves money") 
    
    if "transactionList" not in session:
        session["transactionList"] = {}

    users = {}
    amount_received = {}
    amount_sent = {}
    time = {}
    db = get_db()
    transactions = db.execute('''SELECT * FROM transactions WHERE sender = ? or receiver = ?;''', (user_id, user_id,)).fetchall()
    session["balance"] = round(session["balance"], 2)
    return render_template("bank.html", form=form, balance=session["balance"], transactions=transactions)

#Employee-only page that monitors all bank transactions.
@app.route("/banksystem")
@is_employee
def banksystem():
    db = get_db()
    transactions = db.execute('''SELECT * FROM transactions''').fetchall()
    return render_template("banksystem.html",transactions=transactions)

#Page that lets the user take out a loan to buy more food.
@app.route("/loan", methods=["GET","POST"])
@login_required
def loan():
    form = LoanForm()
    user_id = g.user
    db = get_db()

    if form.validate_on_submit():
        amount = form.amount.data

        #Prevent the user from loaning too much money in one go
        if amount < 1000000:
            
            #Prevent negative loans (no clue why someone would even try but just in case)
            if amount > 0:

                #Passed the checks. Grant the loan.
                currentBal = db.execute(''' SELECT * FROM users
                                    WHERE user_id = ?;''',(user_id,)).fetchone()["balance"]
                db.execute('''UPDATE users
                        SET balance = ?
                        WHERE user_id = ?;''',(currentBal + float(amount), user_id))
                db.commit()
                newBal = db.execute(''' SELECT * FROM users
                                    WHERE user_id = ?;''',(user_id,)).fetchone()["balance"]
                g.balance = newBal
                myStr = "took out a loan of Щ " + str(amount)

                #Log the loan
                eventLogger(user_id, myStr)
                currentTransaction = datetime.datetime.now()
                db.execute('''INSERT INTO transactions(sender, receiver, amount, time_of_transaction)
                        VALUES(?, ?, ?, ?);''', (user_id, "Restaurant Waluigi", -1 * amount, currentTransaction))
                db.commit()
                return redirect( url_for("refresh_balance") )
            
            #Error messages
            else:
                form.amount.errors.append("What are you trying to accomplish??")
                eventLogger(user_id, "Tried to loan money to Waluigi Restaurant")
        else:
            form.amount.errors.append("Are you trying to crash the Waluigi economy or something?")
            eventLogger(user_id, "tried to take a big loan and failed")
    
    return render_template("loan.html", form=form)

#Employee-only page that displays all activity on the site. Site activity is logged with the EventLogger function.
@app.route("/siteactivity")
@is_employee
def siteActivity():
    db = get_db()
    events = db.execute('''SELECT * FROM events''').fetchall()
    return render_template("eventlogger.html", events=events)

#Displays the menu.
@app.route("/menu")
def menu():
    db = get_db()
    menu = db.execute(''' SELECT * FROM menu;''').fetchall()
    return render_template("menu.html",menu=menu)

#Displays the selected food.
@app.route("/food/<int:menu_id>")
def food(menu_id):
    db = get_db()
    food = db.execute(''' SELECT * FROM menu
                            WHERE menu_id=?;''',(menu_id,)).fetchone()
    return render_template("food.html",food=food)

#Displays the cart. Requires login.
@app.route("/cart", methods=["GET","POST"])
@login_required
def cart():
    if "cart" not in session:
        session["cart"] = {}
    
    names = {}
    prices = {}
    subtotals = {}
    total = 0

    db = get_db()
    for menu_id in session["cart"]:
        name = db.execute(''' SELECT * FROM menu
                                WHERE menu_id = ?;''',(menu_id,)).fetchone()["name"]
        names[menu_id] = name
        price = db.execute(''' SELECT * FROM menu
                                WHERE menu_id = ?;''',(menu_id,)).fetchone()["price"]
        prices[menu_id] = price
        subtotal = session["cart"][menu_id] * price
        subtotals[menu_id] = round(subtotal, 2)
        total = round(sum(subtotals.values()), 2)
    return render_template("cart.html", cart=session["cart"], names=names, prices=prices, subtotals=subtotals, total=total)

#Checkout page.
@app.route("/checkout", methods = ['GET', 'POST'])
@login_required
def checkout():

    today = datetime.date.today().strftime("%d/%m/%Y")
    user_id = g.user

    #A repeat of the code from the cart function
    names = {}
    prices = {}
    subtotals = {}
    taxes = {}
    costs = {}
    total = 0
    
    db = get_db()
    for menu_id in session["cart"]:
        
        name = db.execute(''' SELECT * FROM menu
                                WHERE menu_id = ?;''',(menu_id,)).fetchone()["name"]
        names[menu_id] = name

        #Fetch the price.
        price = db.execute(''' SELECT * FROM menu
                                WHERE menu_id = ?;''',(menu_id,)).fetchone()["price"]
        prices[menu_id] = price

        #Calculate the subtotal for this menu item
        subtotal = session["cart"][menu_id] * price
        subtotals[menu_id] = subtotal  
        #Calculate VAT for this item.
        tax = round(subtotal * 0.23, 2)
        taxes[menu_id] = tax

        #Calculate the cost excluding tax
        cost = round(subtotal - tax, 2)
        costs[menu_id] = cost

        #Sum the values of the subtotal dictionary to get the overall total
        total = sum(subtotals.values()) 
        taxTotal = sum(taxes.values())
        costTotal = sum(costs.values())
    
    #Log the purchase
    eventLogger(user_id, "bought some food")
    currentTransaction = datetime.datetime.now()
    db.execute('''INSERT INTO transactions(sender, receiver, amount, time_of_transaction)
                VALUES(?, ?, ?, ?);''', (user_id, "Restaurant Waluigi", float(total), currentTransaction))
    db.commit()
    
    #Update the balance in the database and update the global variable.
    currentBal = db.execute(''' SELECT * FROM users
                            WHERE user_id = ?;''',(user_id,)).fetchone()["balance"]
    db.execute('''UPDATE users
                SET balance = ?
                WHERE user_id = ?;''',(currentBal - float(total), user_id))
    db.commit()
    newBal = db.execute(''' SELECT * FROM users
                            WHERE user_id = ?;''',(user_id,)).fetchone()["balance"]
    g.balance = newBal

    return render_template("checkout.html", cart=session["cart"], 
    names=names, prices=prices, subtotals=subtotals, 
    total=total, today=today, taxes=taxes, costs=costs,
    taxTotal=taxTotal, costTotal=costTotal)

#Add an item to your cart.
@app.route("/add_to_cart/<int:menu_id>")
@login_required
def add_to_cart(menu_id):
    user_id = g.user
    if "cart" not in session:
        session["cart"] = {}
    if menu_id not in session["cart"]:
        session["cart"][menu_id] = 0
    session["cart"][menu_id] = session["cart"][menu_id] + 1
    eventLogger(user_id, "added an item to cart")
    print(session["cart"])
    return redirect( url_for("cart") )

#Remove an item from your cart.
@app.route("/remove_from_cart/<int:menu_id>")
@login_required
def remove_from_cart(menu_id):
    user_id = g.user
    if "cart" not in session:
        session["cart"] = {}
    if menu_id not in session["cart"]:
        session["cart"][menu_id] = 0
    if session["cart"][menu_id] > 0:
        session["cart"][menu_id] = session["cart"][menu_id] - 1
    eventLogger(user_id, "removed an item from their cart")
    print(session["cart"])
    return redirect( url_for("cart") )

#Empty your cart completely.
@app.route("/empty_cart")
@login_required
def empty_cart():
    session["cart"] = {}
    user_id = g.user
    print(session["cart"])
    return redirect( url_for("cart") )

#Empties the cart and refreshes the balance after completing a purchase.
@app.route("/finishedpurchase")
@login_required
def finishedpurchase():
    session["cart"] = {}
    user_id = g.user
    return redirect( url_for("refresh_balance") )

#Refresh your bank balance.
@app.route("/refreshbalance")
@login_required
def refresh_balance():
    user_id = g.user
    db = get_db()
    session["balance"] = db.execute(''' SELECT * FROM users
                        WHERE user_id = ?;''',(user_id,)).fetchone()["balance"]
    eventLogger(user_id, "refreshed their balance")
    db.close()
    
    return redirect( url_for("bankTransfer") )

#Manages the friend system.
@app.route("/friends", methods=["GET","POST"])
@login_required
def friends():

    user_id = g.user
    db = get_db()
    form = FriendForm()
    if form.validate_on_submit():
        friend = form.friend.data
        
        friendUser = db.execute(''' SELECT * FROM users
                            WHERE user_id = ?;''',(friend,)).fetchone()
        
        #Checks if the friend exists.
        if friendUser is None:
            form.friend.errors.append("User doesn't exist.")
        
        #If this condition passes.
        else:
            #Checks if you, as the sender, have any current requests to that user.
            if user_id != friendUser["user_id"]:
                firstTest = db.execute('''SELECT * FROM friendrequests
                                    WHERE sender = ? AND receiver = ?''', (user_id, friendUser["user_id"])).fetchall()
                
                if len(firstTest) == 0:
                    
                    #If you, as the receiver, have any current requests from that user.
                    secondTest = db.execute('''SELECT * FROM friendrequests
                                    WHERE sender = ? AND receiver = ?''', (friendUser["user_id"], user_id)).fetchall()
                    
                    if len(secondTest) == 0:
                        
                        #All conditions passed. Add the friend request to the database.
                        myRequest = db.execute('''INSERT INTO friendrequests(sender, receiver, resolved)
                                                VALUES(?, ?, ?)''', (user_id, friendUser["user_id"], False))
                        db.commit()

                        #Add to site logs.
                        eventLogger(user_id, "added a friend")
                    else:
                        form.friend.errors.append("Invalid request!") 
                else: 
                    form.friend.errors.append("Invalid request!") 
            else:
                #Log someone's eternal loneliness.
                form.friend.errors.append("You are already friends with yourself!") 
                eventLogger(user_id, "tried to befriend themselves")

    #Data needed to handle the friend system on the front-end.           
    sentQueue = db.execute('''SELECT * FROM friendrequests WHERE sender = ? AND resolved = ?;''', (user_id, 0,)).fetchall()
    receivedQueue = db.execute('''SELECT * FROM friendrequests WHERE receiver = ? AND resolved = ?;''', (user_id, 0,)).fetchall()
    friendQueue1 = db.execute('''SELECT * FROM friendrequests WHERE receiver = ? AND resolved = ?;''', (user_id, 1,)).fetchall()
    friendQueue2 = db.execute('''SELECT * FROM friendrequests WHERE sender = ? AND resolved = ?;''', (user_id, 1,)).fetchall()
    return render_template("friends.html", form=form, sentQueue = sentQueue, receivedQueue = receivedQueue, friendQueue1 = friendQueue1, friendQueue2 = friendQueue2)

#Accept a request from someone.
@app.route("/AddFriend/<string:friend>")
@login_required
def AddFriend(friend):
    user_id = g.user
    friend = friend
    db = get_db()
    acceptRequest = db.execute('''UPDATE friendrequests
                                    SET resolved = ?
                                    WHERE sender = ?
                                    AND receiver = ?
                    ''', (True, friend, user_id,))
    db.commit()
    eventLogger(user_id, "accepted a friend request")
    return redirect( url_for("friends") )

#View someone's profile (or your own!)
@app.route("/profile/<string:person>")
@login_required
def profile(person):
    user_id = g.user
    canEdit = False
    biography = None
    pfp = None
    isUser = False

    db = get_db()
    bio = db.execute(''' SELECT * FROM users
                        WHERE user_id = ?;''',(person,)).fetchone()
    if bio:
        biography = bio["bio"]
        pfp = db.execute(''' SELECT * FROM users
                        WHERE user_id = ?;''',(person,)).fetchone()["pfp"]
        
        isUser = True

    if person == g.user:
        
        #Restrict editing to your own profile only.
        canEdit = True
    return render_template("profile.html", person=person, canEdit=canEdit, bio=biography, pfp=pfp, isUser=isUser)

#Edit your profile
@app.route("/editprofile", methods = ['GET', 'POST'])
@login_required
def EditProfile():

    form = EditProfilePage()
    if form.validate_on_submit():
        user_id = g.user
        bio = form.bio.data
        pfp = form.pfp.data
        db = get_db()
        db.execute('''UPDATE users
                    SET pfp = ?, bio = ?
                    WHERE user_id = ?;''',(pfp, bio, user_id))
        db.commit()
        form.bio.errors.append("Changes saved.")

    return render_template("editprofile.html", form=form)
