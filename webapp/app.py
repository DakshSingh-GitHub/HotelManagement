from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector as sql
import mysql.connector.errors
import os
import pickle
from datetime import datetime


class GenderInputException(Exception):
    pass


class DateLimitCheckError(Exception):
    pass


class EndCode(Exception):
    pass


class DateLimitExceedError(Exception):
    pass


class MonthLimitExceedError(Exception):
    pass

class InvalidCustomer(Exception):
    pass

class AgeLimitChecker(Exception):
    pass

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database connection
def get_db_connection():
    conn = sql.connect(
        host="localhost",
        user="root", # CHANGE THIS
        password="root", # CHANGE THIS
        database="hotel",
    )
    return conn

def gstcheck(bill):
    if bill > 7500:
        return 0.18
    else:
        return 0.12

# ######################################## USER #####################################################


Admin_ = "DakshSingh"
AdminPassword = "dakshsingh"


def AuthenticateUser(username, password):
    # This needs to be adapted for web usage. Storing users in a file is not ideal for a web app.
    # For now, we will keep it as it is, but it should be replaced with a proper database-backed user system.
    if not os.path.exists("users.been"):
        with open("users.been", "wb") as f:
            pickle.dump({Admin_: AdminPassword}, f)
    
    with open("users.been", "rb") as f:
        dic = pickle.load(f)
        if username not in dic:
            return False
        elif dic[username] == password:
            return True
        else:
            return False

def CreateUser(username, password):
    if AuthenticateUser(username, password):
        return False, "User Already Exists"
    else:
        with open("users.been", "rb") as f:
            dic = pickle.load(f)
        if len(dic) <= 4:
            dic[username] = password
            os.remove("users.been")
            with open("users.been", "wb") as f:
                pickle.dump(dic, f)
            return True, "User created successful"
        else:
            return False, "User Limit Exceeded"

def DisplayUsers():
    with open("users.been", "rb") as f:
        dic = pickle.load(f)
        return dic

def Admin(username, password):
    if username == Admin_ and password == AdminPassword:
        return True
    else:
        return False


def DeleteUser(userID):
    if userID == Admin_:
        return False, "Admin Can't be Deleted"
    else:
        with open("users.been", "rb") as f:
            dic = pickle.load(f)
        if userID in dic:
            dic.pop(userID)
            os.remove("users.been")
            with open("users.been", "wb") as f:
                pickle.dump(dic, f)
            return True, "User deleted successful"
        else:
            return False, "User Not Found"

def checkAvailableRoom(checkin_date_str: str, room_type: str, conn, cursor, date_format="%Y-%m-%d"):
    """
    Checks the availability of a room based on the check-in date and room type.
    Returns the room ID and tariff if available, otherwise, returns None.
    """
    try:
        checkin_date = datetime.strptime(checkin_date_str, date_format).date()
    except ValueError:
        return None, "Invalid date format for check-in."

    # Get all rooms of the specified type
    cursor.execute(f"SELECT room_id, tariff FROM room WHERE room_type = '{room_type}'")
    possible_rooms = cursor.fetchall()

    if not possible_rooms:
        return None, "No rooms of this type exist."

    # Check each room for availability
    for room_id, tariff in possible_rooms:
        # Check for overlapping bookings
        # A room is occupied if its checkin date is before or on checkin_date, and checkout date is after checkin_date
        query = f"""
            SELECT COUNT(*) FROM booking
            JOIN customer ON booking.guest_id = customer.c_id
            WHERE booking.room_id = {room_id}
            AND customer.checkin <= '{checkin_date_str}' AND customer.checkout > '{checkin_date_str}'
        """
        cursor.execute(query)
        occupied_count = cursor.fetchone()[0]

        if occupied_count == 0:
            return room_id, tariff
    
    return None, "No available rooms of this type for the specified date."

def calculate_bill(customer_id, date_changed_str="2024-01-01", conn=None, cursor=None, date_format="%Y-%m-%d"):
    """
    Calculates a customer's bill based on check-in date and tariff change date.
    Returns a dictionary of bill details.
    """
    if conn is None or cursor is None:
        raise Exception("Database connection and cursor are required.")

    bill_details = {}

    try:
        # Retrieve customer check-in date, checkout date, name, address, gender
        cursor.execute(f"SELECT c_name, address, gender, checkin, checkout, paid FROM customer WHERE c_id = {customer_id}")
        customer_data = cursor.fetchone()
        if not customer_data:
            raise InvalidCustomer("Customer ID does not exist.")
        
        c_name, address, gender_code, checkin_date_db, checkout_date_db, paid_amount = customer_data
        
        gender = "Male" if gender_code in ["M", "m"] else "Female"
        
        checkin_date = datetime.strptime(str(checkin_date_db), "%Y-%m-%d")
        checkout_date = datetime.strptime(str(checkout_date_db), "%Y-%m-%d")

        # Convert date_changed_str to datetime object
        date_changed_dt = datetime.strptime(date_changed_str, date_format)

        # Retrieve room id and tariff from booking table
        cursor.execute(f"SELECT room_id, tariff, discount, service FROM booking WHERE guest_id = {customer_id}")
        booking_data = cursor.fetchone()
        if not booking_data:
            raise Exception("Booking details not found for this customer.")
        
        room_id, booking_tariff, discount, service_id = booking_data

        # Retrieve room type from room table
        cursor.execute(f"SELECT room_type FROM room WHERE room_id = {room_id}")
        room_type = cursor.fetchone()[0]

        # Determine the tariff to use for calculation
        final_tariff = booking_tariff
        if checkin_date < date_changed_dt:
            # Use old tariff (booking_tariff)
            bill_details['tariff_note'] = "Bill calculated using the old tariff."
        else:
            # Use new tariff from room table if checkin is after tariff change
            cursor.execute(f"SELECT tariff FROM room WHERE room_type = '{room_type}'")
            new_tariff_from_room = cursor.fetchone()
            if new_tariff_from_room:
                final_tariff = new_tariff_from_room[0]
                bill_details['tariff_note'] = "Bill calculated using the new tariff."
            else:
                bill_details['tariff_note'] = "Could not find new tariff, using booking tariff."
        
        # Calculate total days of stay
        stay_duration = (checkout_date - checkin_date).days
        if stay_duration == 0:
            stay_duration = 1 # Minimum 1 day stay

        base_bill = final_tariff * stay_duration

        # Apply discount
        discount_amount = base_bill * (discount / 100)
        subtotal = base_bill - discount_amount

        # Apply GST
        gst_percentage = gstcheck(subtotal)
        gst_amount = subtotal * gst_percentage
        total_bill = subtotal + gst_amount

        # Payment status
        remaining_amount = total_bill - (paid_amount if paid_amount else 0)
        payment_status = "FULLY PAID" if remaining_amount <= 0 else "PENDING"

        bill_details.update({
            'customer_id': customer_id,
            'customer_name': c_name,
            'address': address,
            'gender': gender,
            'checkin_date': checkin_date.strftime('%Y-%m-%d'),
            'checkout_date': checkout_date.strftime('%Y-%m-%d'),
            'room_id': room_id,
            'tariff': f"{final_tariff} ({stay_duration} days)",
            'service': service_id, # This needs to be mapped to service name
            'discount': discount,
            'subtotal': round(subtotal, 2),
            'gst_percentage': gst_percentage * 100,
            'gst_amount': round(gst_amount, 2),
            'total_bill': round(total_bill, 2),
            'paid_amount': paid_amount if paid_amount else 0,
            'remaining_amount': round(remaining_amount, 2),
            'payment_status': payment_status
        })
        return bill_details

    except InvalidCustomer as e:
        raise e
    except Exception as e:
        raise Exception(f"Error calculating bill: {e}")


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if AuthenticateUser(username, password):
            session['username'] = username
            if Admin(username, password):
                session['is_admin'] = True
            else:
                session['is_admin'] = False
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('is_admin', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if 'username' not in session or not session.get('is_admin'):
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        success, message = CreateUser(username, password)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        return redirect(url_for('create_user'))
    return render_template('create_user.html')

@app.route('/allot_fare', methods=['GET', 'POST'])
def allot_fare():
    if 'username' not in session or not session.get('is_admin'):
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    if request.method == 'POST':
        try:
            fare_option = request.form['fare_option']
            new_fare = int(request.form['new_fare'])

            if new_fare <= 0:
                raise ValueError("New fare must be a positive number.")

            if fare_option == "1": # Add/Change fare for a specific Room ID
                room_id = int(request.form['room_id'])
                cursor.execute(f"UPDATE room SET tariff = {new_fare} WHERE room_id = {room_id}")
                conn.commit()
                flash(f"Fare for room {room_id} updated successfully to {new_fare}.", 'success')
            elif fare_option == "2": # Change fare for a Room Type
                room_type = request.form['room_type']
                if room_type not in ["np", "s"]:
                    raise ValueError("Invalid room type. Please enter 'np' or 's'.")
                cursor.execute(f"UPDATE room SET tariff = {new_fare} WHERE room_type = '{room_type}'")
                conn.commit()
                flash(f"Fare for room type '{room_type}' updated successfully to {new_fare}.", 'success')
            else:
                raise ValueError("Invalid fare option selected.")
            
            return redirect(url_for('dashboard'))

        except ValueError as e:
            flash(f"Invalid input: {e}", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}. Check your SQL syntax or database schema.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('allot_fare.html')

@app.route('/delete_user', methods=['GET', 'POST'])
def delete_user():
    if 'username' not in session or not session.get('is_admin'):
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        user_id = request.form['user_id']
        success, message = DeleteUser(user_id)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        return redirect(url_for('delete_user'))
    users = DisplayUsers()
    return render_template('delete_user.html', users=users)

@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    if 'username' not in session or not session.get('is_admin'):
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    if request.method == 'POST':
        try:
            room_id = int(request.form['room_id'])
            room_type = request.form['room_type']

            if room_type not in ["np", "s"]:
                raise ValueError("Invalid room type. Please enter 'np' or 's'.")

            # Check if room_id already exists
            cursor.execute(f"SELECT room_id FROM room WHERE room_id = {room_id}")
            existing_room = cursor.fetchone()
            if existing_room:
                flash(f"Room with ID {room_id} already exists.", 'danger')
                return render_template('add_room.html')

            # Get the default tariff based on room type
            tariff = 600 if room_type == "s" else 400

            # Insert the new room into the database
            cursor.execute(f"INSERT INTO room (room_id, room_type, tariff, upgrade) VALUES ({room_id}, '{room_type}', {tariff}, 'up')")
            conn.commit()
            flash(f"Room {room_id} added successfully.", 'success')
            return redirect(url_for('dashboard'))

        except ValueError as e:
            flash(f"Invalid input: {e}", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}. Check your SQL syntax or database schema.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('add_room.html')

@app.route('/view_fares')
def view_fares():
    if 'username' not in session or not session.get('is_admin'):
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    try:
        cursor.execute("SELECT room_id, tariff FROM room")
        rooms = cursor.fetchall()
        return render_template('view_fares.html', rooms=rooms)
    except mysql.connector.errors.ProgrammingError as e:
        flash(f"Database programming error: {e}. Check your SQL syntax or database schema.", 'danger')
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return render_template('view_fares.html', rooms=[])

@app.route('/display_users')
def display_users():
    if 'username' not in session or not session.get('is_admin'):
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))
    users = DisplayUsers()
    return render_template('display_users.html', users=users)

@app.route('/create_booking', methods=['GET', 'POST'])
def create_booking():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    if request.method == 'POST':
        try:
            name = request.form['name']
            address = request.form['address']
            age = int(request.form['age'])
            gender = request.form['gender']
            checkin_str = request.form['checkin']
            checkout_str = request.form['checkout']
            room_type = request.form['room_type']
            
            # Input validation
            if not name or not address or not gender or not checkin_str or not checkout_str or not room_type:
                raise ValueError("All fields are required.")
            if age < 0 or age > 250:
                raise AgeLimitChecker("You 'probably', 'IN MOST CASES', can't live that long.")
            if gender not in ["M", "m", "F", "f"]:
                raise GenderInputException("Enter the Correct Gender (M/F).")

            checkin = datetime.strptime(checkin_str, "%Y-%m-%d")
            checkout = datetime.strptime(checkout_str, "%Y-%m-%d")

            if checkout < checkin:
                raise DateLimitCheckError("Check-in date cannot be greater than check-out date.")

            # Check room availability
            room_id, tariff = checkAvailableRoom(checkin_str, room_type, conn, cursor)
            
            if room_id is None:
                flash(tariff, 'danger') # tariff now holds the error message
                return render_template('create_booking.html')

            # Get next c_id and book_id
            cursor.execute("SELECT MAX(c_id) FROM customer")
            last_c_id = cursor.fetchone()[0]
            c_id = (last_c_id + 1) if last_c_id else 1001

            cursor.execute("SELECT MAX(book_id) FROM booking")
            last_book_id = cursor.fetchone()[0]
            book_id = (last_book_id + 1) if last_book_id else 5001

            discount = 10 if room_type == "s" else 0
            service = 3004 # Defaulting to None service for now, can be added to form later

            sql_customerTable = f"INSERT INTO customer (c_id, c_name, address, age, gender, checkin, checkout, paid) VALUES ({c_id}, '{name}', '{address}', {age}, '{gender}', '{checkin.strftime('%Y-%m-%d')}', '{checkout.strftime('%Y-%m-%d')}', 0)"
            sql_bookingTable = f"INSERT INTO booking (book_id, guest_id, room_id, tariff, service, discount) VALUES ({book_id}, {c_id}, {room_id}, {tariff}, {service}, '{discount}')"
            
            cursor.execute(sql_customerTable)
            # Temporarily disable foreign key checks for insertion order
            cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
            cursor.execute(sql_bookingTable)
            cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
            conn.commit()
            
            flash(f'Booking successful for customer {name}! Your Customer ID is: {c_id}', 'success')
            return redirect(url_for('dashboard'))

        except (ValueError, GenderInputException, DateLimitCheckError, AgeLimitChecker) as e:
            flash(str(e), 'danger')
        except mysql.connector.errors.IntegrityError as e:
            flash(f"Database error: {e}. It's possible a customer or booking ID already exists. Try again.", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}. Check your SQL syntax or database schema.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('create_booking.html')

@app.route('/get_bill', methods=['GET', 'POST'])
def get_bill():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    bill_details = None
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        try:
            customer_id = int(request.form['customer_id'])
            date_changed = request.form.get('date_changed') # Optional field

            if not customer_id:
                raise ValueError("Customer ID is required.")

            # Default date if not provided in the form
            if not date_changed:
                date_changed = "2024-01-01" # Default as in main.py, or could use current date

            bill_details = calculate_bill(customer_id, date_changed, conn, cursor)
            if not bill_details:
                flash("Could not calculate bill. Check customer ID and date.", 'danger')

        except (ValueError, InvalidCustomer) as e:
            flash(f"Input error: {e}", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('get_bill.html', bill_details=bill_details)

@app.route('/get_all_customers')
def get_all_customers():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)
    customers_data = []

    try:
        cursor.execute("SELECT c_id, c_name, address, age, gender, checkin, checkout FROM customer")
        customers_raw = cursor.fetchall()

        for customer in customers_raw:
            c_id, c_name, address, age, gender_code, checkin, checkout = customer
            gender = "Male" if gender_code in ["M", "m"] else "Female"
            
            total_payable = 0.0
            # Attempt to get payable amount from the bill table
            cursor.execute(f"SELECT payable FROM bill WHERE `customer id` = {c_id}")
            payable_data = cursor.fetchone()
            if payable_data:
                total_payable = float(payable_data[0])
                # Apply GST if applicable, similar to calculate_bill
                gst_percent = gstcheck(total_payable)
                total_payable = total_payable + (total_payable * gst_percent)
            
            customers_data.append({
                'c_id': c_id,
                'c_name': c_name,
                'address': address,
                'age': age,
                'gender': gender,
                'checkin': checkin.strftime('%Y-%m-%d'),
                'checkout': checkout.strftime('%Y-%m-%d'),
                'total_payable': round(total_payable, 2)
            })
        
    except mysql.connector.errors.ProgrammingError as e:
        flash(f"Database programming error: {e}.", 'danger')
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", 'danger')
    finally:
        cursor.close()
        conn.close()

    return render_template('get_all_customers.html', customers=customers_data)

@app.route('/update_stay', methods=['GET', 'POST'])
def update_stay():
    if 'username' not in session:
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    if request.method == 'POST':
        try:
            customer_id = int(request.form['customer_id'])
            new_checkout_date_str = request.form['new_checkout_date']

            if not new_checkout_date_str:
                raise ValueError("New checkout date is required.")
            
            new_checkout_date = datetime.strptime(new_checkout_date_str, "%Y-%m-%d")

            # Check if customer_id exists
            cursor.execute(f"SELECT c_id from customer WHERE c_id = {customer_id}")
            customer_exists = cursor.fetchone()
            if not customer_exists:
                raise InvalidCustomer(f"Customer with ID {customer_id} not found.")

            # Get current checkin date to ensure new checkout is not before checkin
            cursor.execute(f"SELECT checkin FROM customer WHERE c_id = {customer_id}")
            current_checkin_str = cursor.fetchone()[0]
            current_checkin = datetime.strptime(str(current_checkin_str), "%Y-%m-%d")

            if new_checkout_date < current_checkin:
                raise DateLimitCheckError("New checkout date cannot be before check-in date.")

            query = f"UPDATE customer SET checkout='{new_checkout_date.strftime('%Y-%m-%d')}' WHERE c_id={customer_id}"
            cursor.execute(query)
            conn.commit()

            flash(f"Stay for customer {customer_id} updated successfully to {new_checkout_date_str}.", 'success')
            return redirect(url_for('dashboard'))

        except (ValueError, InvalidCustomer, DateLimitCheckError) as e:
            flash(f"Invalid input: {e}", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}. Check your SQL syntax or database schema.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('update_stay.html')

@app.route('/get_booking_for_day', methods=['GET', 'POST'])
def get_booking_for_day():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    bookings_data = []
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        try:
            booking_date_str = request.form['booking_date']
            if not booking_date_str:
                raise ValueError("Booking date is required.")
            
            # Validate date format
            booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d").date()

            query = f"""
                SELECT b.book_id, b.guest_id, b.room_id, b.tariff, b.service, b.discount,
                       c.c_name, c.address, c.age, c.gender, c.checkin, c.checkout
                FROM booking b
                JOIN customer c ON b.guest_id = c.c_id
                WHERE c.checkin = '{booking_date_str}'
            """
            cursor.execute(query)
            raw_bookings = cursor.fetchall()

            for booking in raw_bookings:
                (book_id, guest_id, room_id, tariff, service, discount,
                 c_name, address, age, gender_code, checkin_db, checkout_db) = booking
                
                gender = "Male" if gender_code in ["M", "m"] else "Female"
                
                bookings_data.append({
                    'book_id': book_id,
                    'guest_id': guest_id,
                    'room_id': room_id,
                    'tariff': tariff,
                    'service': service,
                    'discount': discount,
                    'c_name': c_name,
                    'address': address,
                    'age': age,
                    'gender': gender,
                    'checkin': checkin_db.strftime('%Y-%m-%d'),
                    'checkout': checkout_db.strftime('%Y-%m-%d')
                })
            
            if not bookings_data:
                flash(f"No bookings found for {booking_date_str}.", 'info')

        except ValueError as e:
            flash(f"Invalid date format: {e}. Please use YYYY-MM-DD.", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('get_booking_for_day.html', bookings=bookings_data)

@app.route('/get_bookings_between_days', methods=['GET', 'POST'])
def get_bookings_between_days():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    bookings_data = []
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        try:
            start_date_str = request.form['start_date']
            end_date_str = request.form['end_date']
            
            if not start_date_str or not end_date_str:
                raise ValueError("Both start and end dates are required.")
            
            # Validate date format
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if start_date > end_date:
                raise ValueError("Start date cannot be after end date.")

            query = f"""
                SELECT b.book_id, b.guest_id, b.room_id, b.tariff, b.service, b.discount,
                       c.c_name, c.address, c.age, c.gender, c.checkin, c.checkout
                FROM booking b
                JOIN customer c ON b.guest_id = c.c_id
                WHERE c.checkin BETWEEN '{start_date_str}' AND '{end_date_str}'
            """
            cursor.execute(query)
            raw_bookings = cursor.fetchall()

            for booking in raw_bookings:
                (book_id, guest_id, room_id, tariff, service, discount,
                 c_name, address, age, gender_code, checkin_db, checkout_db) = booking
                
                gender = "Male" if gender_code in ["M", "m"] else "Female"
                
                bookings_data.append({
                    'book_id': book_id,
                    'guest_id': guest_id,
                    'room_id': room_id,
                    'tariff': tariff,
                    'service': service,
                    'discount': discount,
                    'c_name': c_name,
                    'address': address,
                    'age': age,
                    'gender': gender,
                    'checkin': checkin_db.strftime('%Y-%m-%d'),
                    'checkout': checkout_db.strftime('%Y-%m-%d')
                })
            
            if not bookings_data:
                flash(f"No bookings found between {start_date_str} and {end_date_str}.", 'info')

        except ValueError as e:
            flash(f"Invalid date format or range: {e}. Please use YYYY-MM-DD.", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('get_bookings_between_days.html', bookings=bookings_data)

@app.route('/cancel_booking', methods=['GET', 'POST'])
def cancel_booking():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        try:
            customer_id = int(request.form['customer_id'])

            # Check if customer exists
            cursor.execute(f"SELECT c_id FROM customer WHERE c_id = {customer_id}")
            if not cursor.fetchone():
                raise InvalidCustomer(f"Customer with ID {customer_id} not found.")

            # Get booking details for checkin/checkout dates
            cursor.execute(f"SELECT c.checkin, c.checkout, b.payable FROM customer c JOIN bill b ON c.c_id = b.`customer id` WHERE c.c_id = {customer_id}")
            booking_info = cursor.fetchone()

            if not booking_info:
                flash(f"No booking found for customer ID {customer_id}.", 'danger')
                return render_template('cancel_booking.html')

            checkin_date_db, checkout_date_db, payable_amount = booking_info
            
            # Convert to datetime objects
            checkin_date = datetime.strptime(str(checkin_date_db), "%Y-%m-%d")
            checkout_date = datetime.strptime(str(checkout_date_db), "%Y-%m-%d")
            current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            # Cancellation Logic (simplified from main.py, assuming 'bill' table handles payable)
            if current_date >= checkin_date:
                flash("Booking cannot be cancelled after check-in.", 'danger')
            elif current_date < checkin_date:
                # Calculate cancellation fee (30% of payable amount if before check-in)
                cancellation_fee = payable_amount * 0.30
                
                # Update payable in bill table (main.py updates bill directly)
                cursor.execute(f"UPDATE bill SET payable = {cancellation_fee} WHERE `customer id` = {customer_id}")
                
                # Delete from booking and customer (or just mark as cancelled)
                # For simplicity, we'll delete the booking but keep customer data with updated payable.
                # In a real system, you might have a 'status' column.
                cursor.execute(f"DELETE FROM booking WHERE guest_id = {customer_id}")
                # Optional: Update customer's paid to reflect cancellation fee if not fully paid
                # cursor.execute(f"UPDATE customer SET paid = {cancellation_fee} WHERE c_id = {customer_id}")

                conn.commit()
                flash(f"Booking for customer {customer_id} cancelled successfully. A cancellation fee of Rs. {cancellation_fee:.2f} has been charged (30% of original bill).", 'warning')
            else:
                flash("Booking cannot be cancelled.", 'danger')

            return redirect(url_for('dashboard'))

        except (ValueError, InvalidCustomer) as e:
            flash(f"Input error: {e}", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}. Check your SQL syntax or database schema.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('cancel_booking.html')

@app.route('/booking_counts', methods=['GET', 'POST'])
def booking_counts():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    booking_counts_data = {}
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        try:
            start_date_str = request.form['start_date']
            end_date_str = request.form['end_date']
            
            if not start_date_str or not end_date_str:
                raise ValueError("Both start and end dates are required.")
            
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if start_date > end_date:
                raise ValueError("Start date cannot be after end date.")

            query = f"""
                SELECT DATE(checkin) AS date, COUNT(*) AS booking_count
                FROM customer
                WHERE checkin BETWEEN '{start_date_str}' AND '{end_date_str}'
                GROUP BY date ORDER BY date
            """
            cursor.execute(query)
            results = cursor.fetchall()

            daily_counts = {str(date): count for date, count in results}
            total_bookings = sum(daily_counts.values())

            if total_bookings == 0:
                flash(f"No bookings found between {start_date_str} and {end_date_str}.", 'info')
            else:
                booking_counts_data = {
                    'total_bookings': total_bookings,
                    'daily_counts': daily_counts
                }

        except ValueError as e:
            flash(f"Invalid date format or range: {e}. Please use YYYY-MM-DD.", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('booking_counts.html', booking_counts_data=booking_counts_data)

@app.route('/occupancy', methods=['GET', 'POST'])
def occupancy():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    occupancy_data = {}
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        try:
            occupancy_date_str = request.form['occupancy_date']
            if not occupancy_date_str:
                raise ValueError("Date is required.")
            
            # Validate date format
            occupancy_date = datetime.strptime(occupancy_date_str, "%Y-%m-%d").date()

            # The original main.py `occupancy` function uses the 'bill' table.
            # Assuming 'bill' table has 'check in' and 'check out' columns and 'room id'.
            query = f"""
                SELECT `room id` FROM bill 
                WHERE `check in` <= '{occupancy_date_str}' AND `check out` > '{occupancy_date_str}'
            """
            cursor.execute(query)
            occupied_rooms_raw = cursor.fetchall()
            
            occupied_room_ids = [room[0] for room in occupied_rooms_raw]
            num_occupied_rooms = len(occupied_room_ids)

            if num_occupied_rooms == 0:
                flash(f"No rooms occupied on {occupancy_date_str}.", 'info')
            else:
                occupancy_data = {
                    'num_occupied_rooms': num_occupied_rooms,
                    'occupied_rooms': occupied_room_ids
                }

        except ValueError as e:
            flash(f"Invalid date format: {e}. Please use YYYY-MM-DD.", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}. Check your SQL syntax or database schema.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('occupancy.html', occupancy_data=occupancy_data)

@app.route('/summary', methods=['GET', 'POST'])
def summary():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    summary_report = {}
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        try:
            summary_date_str = request.form.get('summary_date')
            
            target_date = None
            if summary_date_str:
                target_date = datetime.strptime(summary_date_str, "%Y-%m-%d").date()
            else:
                cursor.execute("SELECT CURDATE()")
                target_date = cursor.fetchone()[0]
            
            date_str = target_date.strftime("%Y-%m-%d")

            # Calculate number of check-ins
            cursor.execute(f"SELECT COUNT(*) FROM customer WHERE DATE(checkin) = '{date_str}'")
            num_checkins = cursor.fetchone()[0]

            # Calculate number of check-outs
            cursor.execute(f"SELECT COUNT(*) FROM customer WHERE DATE(checkout) = '{date_str}'")
            num_checkouts = cursor.fetchone()[0]

            # Calculate total revenue and collected revenue
            collected_revenue = 0
            total_expected_revenue = 0

            # Get paid amounts for customers checking out on this date
            cursor.execute(f"SELECT IFNULL(paid, 0) FROM customer WHERE DATE(checkout) = '{date_str}'")
            paid_amounts = cursor.fetchall()
            for paid in paid_amounts:
                collected_revenue += float(paid[0])

            # Get payable amounts from bill for customers checking out on this date
            cursor.execute(f"SELECT payable FROM bill WHERE DATE(`check out`) = '{date_str}'")
            bill_payables = cursor.fetchall()
            for payable in bill_payables:
                bill_amount = float(payable[0])
                total_expected_revenue += bill_amount + (bill_amount * gstcheck(bill_amount))

            summary_report = {
                'date': date_str,
                'num_checkins': num_checkins,
                'num_checkouts': num_checkouts,
                'total_revenue': round(total_expected_revenue, 2),
                'collected_revenue': round(collected_revenue, 2)
            }
            
        except ValueError as e:
            flash(f"Invalid date format: {e}. Please use YYYY-MM-DD.", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('summary.html', summary_report=summary_report)

@app.route('/payment_check', methods=['GET', 'POST'])
def payment_check():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    payment_status_data = {}
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        try:
            customer_id = int(request.form['customer_id'])

            cursor.execute(f"SELECT payable FROM bill WHERE `customer id` = {customer_id}")
            payable_data = cursor.fetchone()
            
            cursor.execute(f"SELECT paid FROM customer WHERE c_id = {customer_id}")
            paid_data = cursor.fetchone()

            if payable_data is None or paid_data is None:
                raise InvalidCustomer(f"No billing or payment information found for customer ID {customer_id}.")
            
            payable_amount = float(payable_data[0])
            paid_amount = float(paid_data[0]) if paid_data[0] is not None else 0.0

            remaining_amount = payable_amount - paid_amount
            status = "FULLY PAID" if remaining_amount <= 0 else "PENDING"

            payment_status_data = {
                'customer_id': customer_id,
                'payable': round(payable_amount, 2),
                'paid': round(paid_amount, 2),
                'remaining': round(remaining_amount, 2),
                'status': status
            }

        except ValueError as e:
            flash(f"Invalid input: {e}", 'danger')
        except InvalidCustomer as e:
            flash(f"Error: {e}", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('payment_check.html', payment_status_data=payment_status_data)

@app.route('/update_paid_amount', methods=['GET', 'POST'])
def update_paid_amount():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        try:
            customer_id = int(request.form['customer_id'])
            amount_paid = float(request.form['amount_paid'])

            if amount_paid <= 0:
                raise ValueError("Amount paid must be a positive number.")

            # Check if customer exists
            cursor.execute(f"SELECT c_id FROM customer WHERE c_id = {customer_id}")
            if not cursor.fetchone():
                raise InvalidCustomer(f"Customer with ID {customer_id} not found.")

            # Get current paid amount and total payable
            cursor.execute(f"SELECT paid FROM customer WHERE c_id = {customer_id}")
            current_paid_data = cursor.fetchone()
            current_paid = float(current_paid_data[0]) if current_paid_data[0] is not None else 0.0

            cursor.execute(f"SELECT payable FROM bill WHERE `customer id` = {customer_id}")
            payable_data = cursor.fetchone()
            if not payable_data:
                raise Exception(f"No bill found for customer ID {customer_id}.")
            total_payable = float(payable_data[0])

            # Apply GST to total_payable for correct comparison
            total_payable_with_gst = total_payable + (total_payable * gstcheck(total_payable))

            new_total_paid = current_paid + amount_paid

            if new_total_paid >= total_payable_with_gst:
                change = new_total_paid - total_payable_with_gst
                cursor.execute(f"UPDATE customer SET paid = {total_payable_with_gst} WHERE c_id = {customer_id}")
                flash(f"Payment completed for customer {customer_id}. Change: Rs. {change:.2f}", 'success')
            else:
                cursor.execute(f"UPDATE customer SET paid = {new_total_paid} WHERE c_id = {customer_id}")
                remaining = total_payable_with_gst - new_total_paid
                flash(f"Amount Rs. {amount_paid:.2f} added to customer {customer_id}'s bill. Remaining: Rs. {remaining:.2f}", 'info')
            
            conn.commit()
            return redirect(url_for('dashboard'))

        except (ValueError, InvalidCustomer) as e:
            flash(f"Input error: {e}", 'danger')
        except mysql.connector.errors.ProgrammingError as e:
            flash(f"Database programming error: {e}.", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('update_paid_amount.html')


if __name__ == '__main__':
    app.run(debug=True)
