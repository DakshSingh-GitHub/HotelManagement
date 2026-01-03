import mysql.connector as sql
import mysql.connector.errors
from colorama import Fore, Style
import time
from datetime import datetime
import pickle
import os


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

def count(c=30):
    """
    A function that counts down from a given number 'c' in minutes and seconds format, displaying a message indicating the remaining time. It uses the 'Fore.BLUE' color to display the countdown message. Once the countdown reaches 0, it displays a message indicating that the login session has expired. This function does not return any value.
    """
    while c:
        m, s = divmod(c, 60)
        text = "Login Session Out in: {:02d}:{:02d}".format(m, s)
        print(Fore.BLUE + text, end="\r")
        time.sleep(1)
        c -= 1
    text = "Login Session Expired [ERR] {MAKE NEW LOGIN SESSION}"
    print(Fore.RED + text)
    print(Style.RESET_ALL, end="")


######################################## USER #####################################################


Admin_ = "DakshSingh"
AdminPassword = "dakshsingh"


def AuthenticateUser(username, password):
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
        print(Fore.RED + "User Already Exists")
    else:
        with open("users.been", "rb") as f:
            dic = pickle.load(f)
        if len(dic) <= 4:
            dic[username] = password
            os.remove("users.been")
            with open("users.been", "wb") as f:
                pickle.dump(dic, f)
            print(Fore.GREEN + "User created successful")
        else:
            print(Fore.RED + "User Limit Exceeded")
        print(Style.RESET_ALL, end='')

def DisplayUsers():
    with open("users.been", "rb") as f:
        dic = pickle.load(f)
        c = 1
        for i in dic:
            if c==1:
                print(Fore.MAGENTA + f"{c}) {i}"+" (Admin)")
                print(Style.RESET_ALL, end='')
            else:
                print(f"{c}) {i}")
            c+=1

def Admin(username, password):
    if username == Admin_ and password == AdminPassword:
        return True
    else:
        return False


def DeleteUser(userID):
    if userID == Admin_:
        print(Fore.RED + "Admin Can't be Deleted")
    else:
        with open("users.been", "rb") as f:
            dic = pickle.load(f)
        if userID in dic:
            dic.pop(userID)
            os.remove("users.been")
            with open("users.been", "wb") as f:
                pickle.dump(dic, f)
            print(Fore.GREEN + "User deleted successful")
        else:
            print(Fore.RED + "User Not Found")
        print(Style.RESET_ALL, end='')


#############################################################################################

for i in range(5):
    # ---------------------------------USER BYPASS LOGIN---------------------------------------- #
    userID: str = str(input(Fore.GREEN + "User: "))
    passwd: str = str(input("Password: "))
    print(Style.RESET_ALL, end="")
    # userID = "DakshSingh"
    # passwd = "dakshsingh"
    # ---------------------------------USER BYPASS LOGIN---------------------------------------- #
    try:
        if AuthenticateUser(userID, passwd):
            conn = sql.connect(
                host="localhost",
                user=Admin_,
                password=AdminPassword,
                database="hotel",
            )

            break
    except mysql.connector.errors.ProgrammingError:
        print(Fore.RED + "Wrong UserId or Password")
        print(Style.RESET_ALL, end="")
else:
    count(5)
    print(Fore.RED + "[DENIED] USER ID OR PASSWORD WRONG")
    print(Style.RESET_ALL, end="")

cursor = conn.cursor(buffered=True)

########################################### CREATE BOOKING ##################################################

c_id = 1001
book_id = 5001
room_id = 2001

s_room = [2002, 2003]
np_room = [2001, 2004]
room_list_indexer_s = 0
room_list_indexer_np = 0


def checkAvailableRoom(checkin: str, date_format="%Y-%m-%d", type="np"):
    """
    This function checks the availability of a room based on the check-in date, room type, and date format.
    It returns the room ID and tariff if available, otherwise, it returns an error message or expiration message.
    """
    global room_list_indexer_s  # UNBOUND ERROR: import from global scope
    global room_list_indexer_np
    global cursor
    cursor.execute("SELECT * FROM av_room")
    roomdata = cursor.fetchall()
    for i in roomdata:
        if tuple(i)[-2] == type:
            date = str(tuple(i)[2])
            try:
                date1 = datetime.strptime(date, date_format)
                date2 = datetime.strptime(checkin, date_format)
            except ValueError:
                return "Invalid date format. Please ensure the dates match the format specified."

            if date1 < date2:
                return [int(tuple(i)[0]), tuple(i)[-1]]  # type: ignore
            else:
                continue
    else:
        if type == "s":
            tariff = 600
            result = [s_room[room_list_indexer_s], tariff]
            room_list_indexer_s += 1
            return result
        elif type == "np":
            tariff = 400
            result = [np_room[room_list_indexer_np], tariff]
            room_list_indexer_np += 1
            return result


def createBooking(date_format="%Y-%m-%d"):
    """
    This function creates a booking for a customer by taking their name, address, age, gender, check-in and check-out dates, service preference, and room preference.
    It then inserts the customer details into the customer table and the booking details into the booking table in the database.
    If an error occurs during the insertion due to access denial or integrity constraints, appropriate error messages are displayed.
    After successful insertion, the changes are committed to the database.
    """
    cursor.execute("SELECT * FROM room")
    try:
        print("Enter '!END' to exit anytime !")
        name: str = str(input(Fore.CYAN + "Enter Name: "))
        if name == "!END":
            raise EndCode
        address: str = str(input("Enter Address: "))
        if address == "!END":
            raise EndCode
        age: int = int(input("Enter Age (!END doesn't work): "))
        if age < 0 or age > 250:
            raise AgeLimitChecker
        gender: str = str(input("Gender (M/F): "))
        if gender == "!END":
            raise EndCode
        if gender not in ["M", "m", "F", "f"]:
            raise GenderInputException

        print(Fore.BLUE + "Check-in Format:-")
        date: int = int(input(Fore.LIGHTBLUE_EX + "Date: "))
        if date > 31:
            raise DateLimitExceedError
        month: int = int(input("Month: "))
        if month > 12:
            raise MonthLimitExceedError
        year: int = int(input("Year: "))
        chc1i = f"{year}-{month}-{date}"
        checkin = datetime.strptime(chc1i, date_format)

        print(Fore.BLUE + "Check-out Format:-")
        date: int = int(input(Fore.LIGHTBLUE_EX + "Date: "))
        if date > 31:
            raise DateLimitCheckError
        month: int = int(input("Month: "))
        if month > 12:
            raise MonthLimitExceedError
        year: int = int(input("Year: "))
        chc2o = f"{year}-{month}-{date}"
        checkout = datetime.strptime(chc2o, date_format)
        # amt: int = int((input("Enter paid amount: ")))

        if checkout >= checkin:
            pass
        else:
            raise DateLimitCheckError

        service: int = int(
            input(
                Fore.CYAN
                + "Enter Service (3001(catering), 3002(full), 3003(evening stay), 3004(None)): "
            )
        )
        type: str = str(input("Room preference (np = 'Normal', s = 'super'): "))
        print(Style.RESET_ALL, end="")

        extractor = checkAvailableRoom(chc1i, type=type)

        room_id = int(list(extractor)[0])  # type: ignore
        tariff = 1000

        if type == "s":
            discount = 10
        else:
            discount = 0

    except EndCode:
        print(Fore.RED + "[END] __main__.createBooking() stopped")

    except TypeError:
        print(Fore.RED + "[ERROR] Invalid Input. Please try again.")

    except ValueError:
        print(
            Fore.RED
            + "[ERROR] Invalid date format. Please ensure the dates match the format specified"
        )
        
    except AgeLimitChecker:
        print(Fore.RED + "[ERROR] You 'probably', 'IN MOST CASES', can't live that long")

    except mysql.connector.errors.InterfaceError:
        print(Fore.RED + "[ERROR] Database connection failed. Please try again.")

    except GenderInputException:
        print(Fore.RED + "Enter the Correct Gender")

    except DateLimitExceedError:
        print(Fore.RED + f"{date} Date Limits should be bound to 31")

    except MonthLimitExceedError:
        print(Fore.RED + f"{month} Month Limits should be bount to 12")

    except DateLimitCheckError:
        print(Fore.RED + "Check-in date cannot be greater than check-out date")

    finally:
        print(Style.RESET_ALL, end="")

    try:
        sql_customerTable = f"INSERT INTO customer (c_id, c_name, address, age, gender, checkin, checkout, paid) VALUES ({c_id}, '{name}', '{address}', {age}, '{gender}', '{checkin}', '{checkout}', 0)"
        sql_bookingTable = f"INSERT INTO booking (book_id, guest_id, room_id, tariff, service, discount) VALUES ({book_id}, {c_id}, {room_id}, {tariff}, {service}, '{discount}')"
        cursor.execute(sql_customerTable)
        cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
        cursor.execute(sql_bookingTable)
        cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
        print(Fore.GREEN + f"[SUCCESS] Booking successful for customer")  # type:ignore

    # except mysql.connector.errors.ProgrammingError:
    #     print("[404] ACCESS DENIED !!")

    except mysql.connector.errors.IntegrityError:
        cursor.execute("SELECT c_id FROM customer")
        data = cursor.fetchall()
        last_book = int(tuple(data[-1])[0])  # type: ignore
        new_book = last_book + 4000
        sql_customerTable = f"INSERT INTO customer (c_id, c_name, address, age, gender, checkin, checkout) VALUES ({last_book + 1}, '{name}', '{address}', {age}, '{gender}', '{checkin}', '{checkout}')"
        sql_bookingTable = f"INSERT INTO booking (book_id, guest_id, room_id, tariff, service, discount) VALUES ({new_book + 1}, {last_book + 1}, {room_id}, {tariff}, {service}, '{discount}')"
        cursor.execute(sql_customerTable)
        cursor.execute(sql_bookingTable)
        print(Fore.GREEN + f"[SUCCESS] Booking successful for customer")  # type:ignore
        print("Your Customer ID is: " + str(last_book + 1))

    except UnboundLocalError:
        print(Fore.RED + "[ERROR] can't access some variables")


    finally:
        print(Style.RESET_ALL, end="")

    conn.commit()


########################################## ALTERATION #####################################################


def updateStay(c_id, newDate, date_format="%Y-%m-%d"):
    """
    A function that updates the checkout date of a customer in the database.

    Parameters:
        c_id (int): The customer ID.
        newDate (str): The new checkout date in the format specified by date_format.
        date_format (str, Optional): The format of the newDate string (default is "%Y-%m-%d").

    Returns:
        None
    """
    date = datetime.strptime(newDate, date_format)
    cursor.execute("SELECT c_id from customer")
    data = cursor.fetchall()
    d = []
    for i in data: d.append(i[0])
    if c_id not in d:
        raise InvalidCustomer("Invalid customer ID")
    else:
        query = f"UPDATE customer SET checkout='{date}' WHERE c_id={c_id}"
        cursor.execute(query)
        conn.commit()

        print(
            Fore.GREEN
            + f"[SUCCESS] Stay of customer {c_id} has successfully been changed to {date}"
        )
        print(Style.RESET_ALL, end="")


def occupancy(date, date_format="%Y-%m-%d"):
    """
    Retrieves the room IDs of rooms occupied on a specific date.

    Args:

        date (str): The date for which occupied rooms are to be retrieved, in the format '%Y-%m-%d'.
        date_format (str, optional): The format of the 'date' parameter. Defaults to '%Y-%m-%d'.

    Returns:
        list: A list of room IDs occupied on the specified date.
    """
    date = (str(datetime.strptime(date, date_format)))[0:10]
    query = f"SELECT `room id` FROM bill WHERE `check in` <= '{date}' AND `check out` > '{date}'"
    cursor.execute(query)
    occupied_rooms = [room_id for room_id in cursor.fetchall()]
    if len(occupied_rooms) == 0:
        return "No Rooms Occupied"
    return len(occupied_rooms)


def allot_fare():
    """
    Allows the admin to either add a fare to a room or change the fare for a room type.
    """
    ch = input(
        Fore.CYAN
        + "Do you want to (1) add fare to a room or (2) change fare for a room type? "
    )
    if ch == "1":
        room_id = int(input(Fore.CYAN + "Enter the room ID: "))
        cursor.execute(f"SELECT room_id, tariff FROM room WHERE room_id = '{room_id}'")

        data = cursor.fetchall()
        if data == []: pass
        else: print(f"Room ID " + Fore.YELLOW + f"{data[0][0]}" + Fore.CYAN + f" has current rent set to" + Fore.YELLOW + f"{data[0][1]}INR")

        new_fare = int(input(Fore.CYAN + "Enter the new fare: "))
        cursor.execute(
            f"UPDATE room SET tariff = {new_fare} WHERE `room_id` = {room_id}"
        )
        conn.commit()

        print(Fore.GREEN + f"Fare for room {room_id} updated successfully.")
        print(Style.RESET_ALL, end="")

    elif ch == "2":
        room_type = input(Fore.CYAN + "Enter the room type (np or s): ")
        cursor.execute(f"SELECT room_id, tariff FROM room WHERE room_type = '{room_type}'")

        data = cursor.fetchall()
        if data == []: pass
        else:
            print("Room ID\t|\tTariff")
            for i in data:
                print(f"{i[0]}\t|\t{i[1]}")

        new_fare = int(input(Fore.CYAN + "Enter the new fare: "))
        cursor.execute(
            f"UPDATE room SET tariff = {new_fare} WHERE room_type = '{room_type}'"
        )
        conn.commit()

        print(Fore.GREEN + f"Fare for room type {room_type} updated successfully.")
        print(Style.RESET_ALL, end="")

    else:
        print(Fore.RED + "Invalid choice.")
        print(Style.RESET_ALL, end="")


def get_tariff(room_type):
    """
    Retrieves the tariff for a specific room type from the database.

    Args:
        room_type (str): The room type (e.g., 'np' for normal, 's' for super).

    Returns:
        int: The tariff for the specified room type, or -1 if the room type is not found.
    """
    cursor.execute(f"SELECT tariff FROM room WHERE room_type = '{room_type}'")
    result = cursor.fetchone()
    return result[0]

def get_tariff_for_all_rooms():
    cursor.execute("SELECT room_id, tariff FROM room")
    result = cursor.fetchall()
    if result == []: pass
    else:
        print(Fore.GREEN + "Room ID\t|\tTariff")
        for i in result:
            print(f"{i[0]}\t|\t{i[1]}")
    print(Style.RESET_ALL, end="")


def calculate_bill(customer_id, date_changed="2024-01-01", date_format="%Y-%m-%d"):
    """
    Calculates a customer's bill based on check-in date and tariff change date.

    This function retrieves customer and booking details from the database,
    compares the customer's check-in date with the date the tariff was changed,
    and calculates the bill accordingly. If the check-in date is before the
    tariff change date, the old tariff is used; otherwise, the new tariff is used.

    Args:
        customer_id (int): The ID of the customer.
        date_changed (str): The date the tariff was changed, in the format specified by date_format.
        date_format (str, optional): The format of the date_changed string (default is "%Y-%m-%d").

    Returns:
        None: Prints the bill details to the console.
    """
    try:
        # Retrieve customer check-in date
        cursor.execute(f"SELECT checkin FROM customer WHERE c_id = {customer_id}")
        checkin_date_str = cursor.fetchone()[0]
        checkin_date = datetime.strptime(str(checkin_date_str), "%Y-%m-%d")

        # Convert date_changed to datetime object
        date_changed_dt = datetime.strptime(date_changed, date_format)

        # Retrieve room type and tariff from booking table
        cursor.execute(
            f"SELECT room_id, tariff FROM booking WHERE guest_id = {customer_id}"
        )
        room_id, tariff = cursor.fetchone()

        # Retrieve room type from room table
        cursor.execute(f"SELECT room_type FROM room WHERE room_id = {room_id};")
        room_type = cursor.fetchone()[0]

        # Check if check-in date is before tariff change date
        if checkin_date < date_changed_dt:
            # Use old tariff
            bill = tariff
            print(Fore.YELLOW + "Bill calculated using the old tariff.")
        else:
            # Use new tariff
            new_tariff = get_tariff(room_type)
            bill = new_tariff
            print(Fore.YELLOW + "Bill calculated using the new tariff.")

        # Print bill details
        try:
            query1 = f"SELECT * FROM bill WHERE `customer id`={id}"
            cursor.execute(query1)
            customer = cursor.fetchone()
            query2 = f"SELECT * FROM customer WHERE `c_id`={id}"
            query4 = (
                f"SELECT `service package` FROM customer_list WHERE `customer id`={id}"
            )

            gst = gstcheck(bill)
            bill = bill + bill * gst

            cursor.execute(query2)
            CID = cursor.fetchone()

            cursor.execute(query4)
            c_list = cursor.fetchone()

            customer += (bill,)  # type: ignore

            # Calculate the final bill amount including GST
            # Print the bill in a proper format
            print(Fore.CYAN + "-----------------------------------")
            print("Hotel Shahi Rajdarbar".upper())
            print("-----------------------------------")
            print(f"Customer ID: {id}")
            print(f"Name: {tuple(customer)[1]}")
            print(f"Address: {tuple(CID)[2]}")  # type: ignore
            gen = tuple(CID)[5]  # type: ignore
            if gen in ["M", "m"]:
                gen = "Male"
            else:
                gen = "Female"
            print(f"Gender: {gen}")  # type: ignore
            print(f"Check-in Date: {tuple(CID)[3]}")  # type: ignore
            print(f"Check-out Date: {tuple(CID)[4]}")  # type: ignore
            print(f"Room ID: {tuple(customer)[2]}")
            print(f"Tariff: {bill}")  # type: ignore
            print(f"Service: {tuple(c_list)[0]}")  # type: ignore
            print(f"Discount: {tuple(customer)[7]}%")
            print("-----------------------------------")
            print(f"Subtotal: Rs. {bill - bill * (tuple(customer)[7]/100)}")  # type: ignore
            print(f"GST ({gst*100}%): Rs. {bill * gst}")
            print("-----------------------------------")
            print(f"Total Bill: Rs. {bill}")
            print("-----------------------------------")
            print(Style.RESET_ALL, end="")

        except TypeError as e:
            print(Fore.RED + "Customer ID does not exist.")
            print(Style.RESET_ALL, end="")
    except Exception as e:
        print(Fore.RED + f"An error occurred: {e}")
        print(Style.RESET_ALL, end="")


def gets_bill(customer_id):
    try:
        print(Fore.BLUE + "Date Changed Format (Enter '0' if not changed):-")
        date: int = int(input(Fore.LIGHTBLUE_EX + "Date: "))
        if date > 31:
            raise DateLimitExceedError
        month: int = int(input("Month: "))
        if month > 12:
            raise MonthLimitExceedError
        year: int = int(input("Year: "))
        if date == 0 and month == 0 and year == 0:
            calculate_bill(customer_id)
        else:
            chc1i = f"{year}-{month}-{date}"
            date_changed = datetime.strptime(chc1i, "%Y-%m-%d")
            calculate_bill(customer_id, date_changed)
    except DateLimitExceedError:
        print(Fore.RED + f"{date} Date Limits should be bound to 31")
    except MonthLimitExceedError:
        print(Fore.RED + f"{month} Month Limits should be bount to 12")
    finally:
        print(Style.RESET_ALL, end="")


def right_date(date):
    try:
        print(Fore.BLUE + "Reservations for " + str(date))
        dates = date.split("-")
        if int(dates[2]) > 31:
            raise DateLimitExceedError
        if int(dates[1]) > 12:
            raise MonthLimitExceedError
        else:
            return True
    except DateLimitExceedError:
        print(Fore.RED + f"{dates[0]} Date Limits should be bound to 31")
        return False

    except MonthLimitExceedError:
        print(Fore.RED + f"{dates[1]} Month Limits should be bount to 12")
        return False
    finally:
        print(Style.RESET_ALL, end="")


def bug_temp_get_bill(customer_id):
    cursor.execute(f"SELECT * FROM bill WHERE `customer id`={customer_id}")
    bills = cursor.fetchall()
    cursor.execute(f"SELECT address, gender, IFNULL(paid,0) from customer where c_id={customer_id}")
    addresses = cursor.fetchall()
    c = 0
    for bill in bills:
        print(bill)
        print(Fore.CYAN + "-----------------------------------")
        print("Hotel Shahi Rajdarbar".upper())
        print("-----------------------------------")
        print(f"Customer ID: {bill[0]}")
        print(f"Name: {bill[1]}")
        print(f"Address: {addresses[c][0]}")  # type: ignore
        gen = addresses[c][1]  # type: ignore
        if gen in ["M", "m"]:
            gen = "Male"
        else:
            gen = "Female"
        print(f"Gender: {gen}")  # type: ignore
        print(f"Check-in Date: {bill[4]}")  # type: ignore
        print(f"Check-out Date: {bill[5]}")  # type: ignore
        print(f"Room ID: {bill[2]}")
        print(f"Tariff: {bill[4]}")  # type: ignore
        print(f"Service: {bill[10]}")  # type: ignore
        print(f"Discount: {bill[9]}%")
        print("-----------------------------------")
        print(f"Subtotal: Rs. {bill[8]}")  # type: ignore
        # print(f"GST ({gst*100}%): Rs. {bill * gst}")
        print("-----------------------------------")
        print(f"Current Paid Amount: {addresses[c][2]}")
        remaining = int(bill[-1]) - int(addresses[c][2])
        
        if remaining <= 0 or remaining > int(bill[-1]):
            print(Fore.GREEN + f"CHECKOUT")
            print(f"Remaining Amount: {remaining}")
        elif remaining < int(bill[8]):
            print(Fore.RED + f"No CHECKOUT UNLESS BILL IS PAID")
            print(f"Remaining Amount: {remaining}")
        print(f"Total Bill: Rs. {bill[-1]}")
        print("-----------------------------------")
        c += 1
        print(Style.RESET_ALL, end="")

################################################ GET BOOKINGS ############################################
def getBookingForDay(date, date_format="%Y-%m-%d"):
    """
    Retrieves all bookings and customers for a specific day from the database.

    Args:
        date (str): The date for which bookings are to be retrieved, in the format '%Y-%m-%d'.
        date_format (str, optional): The format of the 'date' parameter. Defaults to '%Y-%m-%d'.

    Returns:
        None: This function does not return anything. Instead, it prints the fetched data to the console.
    """
    date = (str(datetime.strptime(date, date_format)))[0:10]
    query = f"SELECT * FROM booking, customer WHERE customer.c_id=booking.guest_id AND customer.checkin='{date}'"
    cursor.execute(query)
    data = cursor.fetchall()
    if data == []:
        print(Fore.GREEN + "No bookings found for the given date.")
        print(Style.RESET_ALL, end="")
    else:
        cid = 1
        print(Fore.LIGHTMAGENTA_EX, end="")
        for i in data:
            cursor.execute(
                f"SELECT checkin, checkout FROM customer WHERE c_id={1000+cid}"
            )
            data = cursor.fetchone()
            if data == []:
                cid += 1
                continue
            else:
                print(Fore.RED + "------------------------------------------------")
                print(Fore.CYAN + "Booking ID: " + str(tuple(i)[0]))
                print("Guest ID: " + str(tuple(i)[1]))
                print("Customer Name: " + str(tuple(i)[7]))
                print("Address: " + str(tuple(i)[8]))
                gen = str(tuple(i)[11])
                if gen in ["M", "m"]:
                    gen = "Male"
                else:
                    gen = "Female"
                print("Gender: " + gen)
                print("Age: " + str(tuple(i)[12]))
                print("Room ID: " + str(tuple(i)[2]))
                print("Booking Tariff: " + str(tuple(i)[3]))
                print("Service ID: " + str(tuple(i)[4]))
                print("Check In: " + str(tuple(data)[0]))
                print("Check Out: " + str(tuple(data)[1]))
                print(Fore.RED + "------------------------------------------------")
        print(Style.RESET_ALL, end="")


def getBookingBetweenDays(start_date, end_date, date_format="%Y-%m-%d"):
    """
    Retrieves all bookings and customers for a specific date range from the database.

    Args:
        start_date (str): The start date of the date range, in the format '%Y-%m-%d'.
        end_date (str): The end date of the date range, in the format '%Y-%m-%d'.
        date_format (str, optional): The format of the date parameters. Defaults to '%Y-%m-%d'.

    Returns:
        None: This function does not return anything. Instead, it prints the fetched data to the console.
    """
    start_date = (str(datetime.strptime(start_date, date_format)))[0:10]
    end_date = (str(datetime.strptime(end_date, date_format)))[0:10]
    query = f"SELECT * FROM booking, customer WHERE customer.c_id=booking.guest_id AND customer.checkin BETWEEN '{start_date}' AND '{end_date}'"
    cursor.execute(query)
    data = cursor.fetchall()
    if data == []:
        print(Fore.GREEN + "No bookings found between the given dates.")
        print(Style.RESET_ALL, end="")
    else:
        print(Fore.LIGHTMAGENTA_EX, end="")
        c = 1
        for i in data:
            cursor.execute(
                f"SELECT checkin, checkout FROM customer WHERE c_id={1000+c}"
            )
            data = cursor.fetchone()
            if data == []:
                c += 1
                continue
            else:
                print(Fore.RED + "------------------------------------------------")
                print(Fore.CYAN + "Booking ID: " + str(tuple(i)[0]))
                print("Guest ID: " + str(tuple(i)[1]))
                print("Customer Name: " + str(tuple(i)[7]))
                print("Address: " + str(tuple(i)[8]))
                gen = str(tuple(i)[11])
                if gen in ["M", "m"]:
                    gen = "Male"
                else:
                    gen = "Female"
                print("Gender: " + gen)
                print("Age: " + str(tuple(i)[12]))
                print("Room ID: " + str(tuple(i)[2]))
                print("Booking Tariff: " + str(tuple(i)[3]))
                print("Service ID: " + str(tuple(i)[4]))
                print("Check In: " + str(tuple(data)[0]))
                print("Check Out: " + str(tuple(data)[1]))
                print(Fore.RED + "------------------------------------------------")


def deleteCustomerByID():
    """
    Deletes a customer from the database by their customer ID.

    Returns:
        None
    """
    global room_list_indexer_np
    global room_list_indexer_s
    c_id = int(input("Enter customer ID: "))
    query = f"DELETE FROM customer WHERE c_id={c_id}"
    cursor.execute(query)
    conn.commit()
    query = f"DELETE FROM booking WHERE guest_id={c_id}"
    cursor.execute(query)
    conn.commit()
    room_list_indexer_s -= 1
    room_list_indexer_np -= 1


# Function to retrieve the number of bookings for each day within the specified date range
def get_booking_counts(start_date, end_date):
    query = f"""
        SELECT DATE(checkin) AS date, COUNT(*) AS booking_count
        FROM customer
        WHERE checkin BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY date
    """
    try:
        date1 = start_date.split("-")[-1]
        month1 = start_date.split("-")[1]
        if int(date1) > 31:
            raise DateLimitExceedError
        if int(month1) > 12:
            raise MonthLimitExceedError

        date2 = end_date.split("-")[-1]
        month2 = end_date.split("-")[1]
        if int(date2) > 31:
            raise DateLimitExceedError
        if int(month2) > 12:
            raise MonthLimitExceedError

        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return "Booking Count -> " + str(len(results))
        except IndexError as e:
            print("Check the dates\n\t1) Either they are same\n\t2) Or they are invalid")
    
    except MonthLimitExceedError:
        print("Check Month")
    
    except DateLimitExceedError:
        print('Check Date')


def cancelbooking(c_id, date_format="%Y-%m-%d"):
    cursor.execute("SELECT curdate()")
    date = datetime.strptime(tuple(cursor.fetchone())[0], date_format)
    cursor.execute(f"SELECT `checkout` from bill where `customer id` = {c_id}")
    checkoutdate = cursor.fetchone()
    cursor.execute(f"SELECT `checkin` from bill where `customer id` = {c_id}")
    checkindate = cursor.fetchone()
    if checkoutdate < date:
        cursor.execute(f"DELETE from bill where `customer id` = {c_id}")
        cursor.execute(f"DELETE from booking where `guest id` = {c_id}")
        print(Fore.RED + "Booking cancelled successfully.")
        staydays = date - tuple(checkindate)[0]
        updateStay(c_id, staydays)
        print(Style.RESET_ALL, end="")
    elif checkindate > date:
        cursor.execute(f"SELECT `payable` from bill where `customer id` = {c_id}")
        bill = cursor.fetchone()
        bill = tuple(bill)[0] * 0.3
        cursor.execute(
            f"UPDATE bill SET `payable` = {bill} where `customer id` = {c_id}"
        )
        print(Fore.RED + "Booking cancelled successfully.")
        print(Fore.RED + "30% of the total amount will be charged as cancellation fee.")
        print(Style.RESET_ALL, end="")
    else:
        print(Fore.RED + "Booking cannot be cancelled.")
        print(Style.RESET_ALL, end="")


def deleteBooking(book_id):
    """
    Deletes a booking from the database by its booking ID.

    Args:
        book_id (int): The booking ID to delete.

    Returns:
        None
    """
    query = f"DELETE FROM booking WHERE book_id={book_id}"
    cursor.execute(query)
    conn.commit()
    print(Fore.RED + "Booking deleted successfully.")
    print(Style.RESET_ALL, end="")


def add_room():
    """
    Prompts the admin for room details and adds a new room to the database.
    """
    try:
        room_id = int(input(Fore.CYAN + "Enter the room ID: "))
        # Check if room_id already exists
        cursor.execute(f"SELECT `room_id` FROM room WHERE `room_id` = {room_id}")
        existing_room = cursor.fetchone()
        if existing_room:
            print(Fore.RED + f"Room with ID {room_id} already exists.")
            print(Style.RESET_ALL, end="")
            return

        room_type = input(Fore.CYAN + "Enter the room type (np or s): ")
        if room_type not in ["np", "s"]:
            print(Fore.RED + "Invalid room type. Please enter 'np' or 's'.")
            print(Style.RESET_ALL, end="")
            return

        # Get the default tariff based on room type
        if room_type == "s":
            tariff = 600
        else:
            tariff = 400

        # Insert the new room into the database
        cursor.execute(
            f"INSERT INTO room (`room_id`, room_type, tariff, upgrade) VALUES ({room_id}, '{room_type}', {tariff}, 'up')"
        )
        conn.commit()
        print(Fore.GREEN + f"Room {room_id} added successfully.")
        print(Style.RESET_ALL, end="")

    except ValueError:
        print(Fore.RED + "Invalid input. Please enter valid details.")
        print(Style.RESET_ALL, end="")


################################################## GST CHECK #####################################################


def gstcheck(bill):
    if bill > 7500:
        return 0.18
    else:
        return 0.12


def getAllCustomers(date_format="%Y-%m-%d"):
    """
    Retrieves all customers from the 'customer' table and their corresponding bills.
    For each customer, the function retrieves the 'payable' value from the 'bill' table
    based on the customer's 'customer id'. The 'payable' value is then modified by
    applying the GST (Goods and Services Tax) using the 'gstcheck' function.
    The modified 'payable' value is appended to the customer's tuple and printed.

    Parameters:
        None

    Returns:
        None
    """
    cursor.execute("SELECT * FROM customer")
    data = cursor.fetchall()

    cursor.execute("SELECT checkin, checkout FROM customer")
    dates = cursor.fetchall()
    if data == []:
        print(Fore.GREEN + "No customers found.")
        print(Style.RESET_ALL, end="")
    else:
        c = 1
        for i in data:
            try:
                cursor.execute(
                    f"SELECT checkin, checkout FROM customer WHERE c_id = {1000+c}"
                )
                dates = cursor.fetchone()
                checkindate = str(tuple(dates)[0])
                checkoutdate = str(tuple(dates)[1])
                c_id = tuple(i)[0]
                query = f"SELECT `payable` FROM bill WHERE `customer id`={c_id}"
                cursor.execute(query)
                price = float(tuple(cursor.fetchone())[0])  # type: ignore
                gst = gstcheck(price)
                price = price + price * gst
                i = tuple(i) + (price,)
                print(Fore.RED + f"------------Customer List {1000+c}------------")
                print(Fore.CYAN, end="")
                print("Customer ID: " + str(i[0]))
                print("Customer Name: " + str(i[1]))
                print("Age: " + str(i[6]))
                gen = str(i[5])
                if gen in ["M", "m"]:
                    gen = "Male"
                else:
                    gen = "Female"
                print("Gender: " + gen)
                print("Address: " + str(i[2]))
                # dt = datetime.strptime(str(i[4]), date_format)
                print("Check In Date: " + checkindate)  # type: ignore
                # del dt
                # dt = datetime.strptime(str(i[5]), date_format)
                print("Check Out Date: " + checkoutdate)  # type: ignore
                print("Total Payable Amount: " + str(i[9]))
                print(Fore.RED + f"-------------------------------------------")
            except:
                c += 1
                cursor.execute(
                    f"SELECT checkin, checkout FROM customer WHERE c_id = {1000+c}"
                )
                dates = cursor.fetchone()
                checkindate = str(tuple(dates)[0])
                checkoutdate = str(tuple(dates)[1])
                c_id = tuple(i)[0]
                query = f"SELECT `payable` FROM bill WHERE `customer id`={c_id}"
                cursor.execute(query)
                price = float(tuple(cursor.fetchone())[0])  # type: ignore
                gst = gstcheck(price)
                price = price + price * gst
                i = tuple(i) + (price,)
                print(Fore.RED + f"------------Customer List {1000+c}------------")
                print(Fore.CYAN, end="")
                print("Customer ID: " + str(i[0]))
                print("Customer Name: " + str(i[1]))
                print("Age: " + str(i[6]))
                gen = str(i[5])
                if gen in ["M", "m"]:
                    gen = "Male"
                else:
                    gen = "Female"
                print("Gender: " + gen)
                print("Address: " + str(i[2]))
                print("Check In Date: " + checkindate)  # type: ignore
                # del dt
                # dt = datetime.strptime(str(i[5]), date_format)
                print("Check Out Date: " + checkoutdate)  # type: ignore
                print("Total Payable Amount: " + str(i[8]))
                print(Fore.RED + f"------------------------------------------")
            print(Style.RESET_ALL, end="")
            c += 1


################################################### Payment ##################################################


def payment_check(c_id):
    """
    Checks if a customer's payment is fully paid based on their customer ID.

    Args:
        c_id (int): The customer ID.

    Returns:
        bool: True if the payment is fully paid, False otherwise.
    """
    cursor.execute(f"SELECT `payable` FROM bill WHERE `customer id` = {c_id}")
    payable = cursor.fetchone()
    cursor.execute(f"SELECT `paid` FROM customer WHERE `c_id` = {c_id}")
    paid = cursor.fetchone()
    if payable == None or paid == None:
        raise TypeError
    else:
        if payable == paid:
            print(Fore.GREEN + f"Payment for customer {c_id} is fully paid.")
            print(Style.RESET_ALL, end="")
            return True
        else:
            print(Fore.RED + f"Payment for customer {c_id} is not fully paid.")
            print(Style.RESET_ALL, end="")
            return False



def update_bill(c_id, amount):
    """
    Updates the amount paid by a customer.
    """
    cursor.execute(f"SELECT `paid` FROM customer WHERE `c_id` = {c_id}")
    paid = cursor.fetchone()
    if paid[0] == None:
        paid = 0
        print("Paid Amount: " + str(paid + amount))

        cursor.execute(f"SELECT `payable` FROM bill WHERE `customer id` = {c_id}")
        payable = cursor.fetchone()

        if int(paid) == int(payable[0]):
            print(Fore.RED + f"Bill for customer {c_id} is already paid.")
            print(Style.RESET_ALL, end="")
        elif amount > (int(payable[0]) - int(paid)):
            print(Fore.RED + f"Payment amount cannot be greater than the payable amount.")
            print("Hand Over Change of " + str(int(amount) - int(payable[0]) + int(paid)))
            if int(amount) - int(payable[0]) + int(paid) > 0:
                cursor.execute(f"UPDATE customer SET `paid` = {int(paid) + amount} WHERE `c_id` = {c_id}")
                conn.commit()
                print("Payable remaining amount is " + str(int(payable[0]) - int(paid) - int(amount)))
            else:
                cursor.execute(f"UPDATE customer SET `paid` = {int(payable[0])} WHERE `c_id` = {c_id}")
                conn.commit()
            print(Style.RESET_ALL, end="")

        else:
            cursor.execute(
                f"UPDATE customer SET `paid` = {int(paid) + amount} WHERE `c_id` = {c_id}"
            )
            conn.commit()
            print(Fore.GREEN + f"Bill for customer {c_id} updated successfully.")
            print(Style.RESET_ALL, end="")
    else:
        cursor.execute(f"SELECT `paid` FROM customer WHERE `c_id` = {c_id}")
        paid = cursor.fetchone()
        print("Current Amount: " + str(paid[0]))

        cursor.execute(f"SELECT `payable` FROM bill WHERE `customer id` = {c_id}")
        payable = cursor.fetchone()

        if int(paid[0]) == int(payable[0]):
            print(Fore.RED + f"Bill for customer {c_id} is already paid.")
            print(Style.RESET_ALL, end="")
        elif amount > (int(payable[0]) - int(paid[0])):
            print(Fore.RED + f"Payment amount cannot be greater than the payable amount.")
            print("Hand Over Change of " + str(int(amount) - int(payable[0]) + int(paid[0])))
            if int(amount) - int(payable[0]) + int(paid[0]) > 0:
                cursor.execute(f"UPDATE customer SET `paid` = {int(paid[0]) + amount} WHERE `c_id` = {c_id}")
                conn.commit()
            else:
                cursor.execute(f"UPDATE customer SET `paid` = {int(payable[0])} WHERE `c_id` = {c_id}")
                conn.commit()
            print(Style.RESET_ALL, end="")

        else:
            cursor.execute(
                f"UPDATE customer SET `paid` = {int(paid[0]) + amount} WHERE `c_id` = {c_id}"
            )
            conn.commit()
            print(Fore.GREEN + f"Bill for customer {c_id} updated successfully.")
            print(Style.RESET_ALL, end="")


############################################### MENU ################################################## 


def summary(date=None, date_format="%Y-%m-%d"):
    """
    Provides a summary of hotel activities for a given date, including:

    - Number of check-ins
    - Number of check-outs
    - Total revenue generated (including GST)

    If no date is provided, the summary will be for the current day.

    Args:
        date (str, optional): The date for which to generate the summary,
                              in the format specified by `date_format`.
                              Defaults to None, which implies the current date.
        date_format (str, optional): The format of the `date` string.
                                     Defaults to "%Y-%m-%d".

    Returns:
        None: Prints the summary to the console.
    """

    if date is None:
        cursor.execute("SELECT CURDATE()")
        date = cursor.fetchone()[0]  # Get current date from the database
    else:
        date = datetime.strptime(date, date_format)

    date_str = date.strftime(date_format)  # Format date for SQL queries

    # Calculate number of check-ins
    cursor.execute(f"SELECT COUNT(*) FROM customer WHERE DATE(checkin) = '{date_str}'")
    num_checkins = cursor.fetchone()[0]

    # Calculate number of check-outs
    cursor.execute(f"SELECT COUNT(*) FROM customer WHERE DATE(checkout) = '{date_str}'")
    num_checkouts = cursor.fetchone()[0]

    # Calculate total revenue (including GST)
    cursor.execute(f"SELECT sum(paid) from customer where DATE(`checkout`) = '{date_str}'")
    paid = cursor.fetchall()
    collected = 0
    total_revenue = 0
    cursor.execute(f"SELECT `payable` FROM bill WHERE DATE(`check out`) = '{date_str}'")
    bills = cursor.fetchall()
    c = 0
    for bill_amount in bills:
        total_revenue += float(bill_amount[0]) * (1 + gstcheck(float(bill_amount[0])))
        collected += int(paid[c][0])
        c += 1

    # Print the summary
    print(Fore.CYAN + f"Summary for {date_str}:")
    print(f"  Number of check-ins: {num_checkins}")
    print(f"  Number of check-outs: {num_checkouts}")
    print(f"  Total revenue: Rs. {total_revenue:.2f}")
    print(f"  Collected revenue: {collected}")
    print(Style.RESET_ALL, end="")


def AdminMenu():
    """
    Display a menu of options and prompt the user to choose one.

    Returns:
        int: The user's choice as an integer.

    Raises:
        ValueError: If the user's input is not a valid integer.
    """
    print("---------------------HOTEL SHAHI RAJDARBAR---------------------")
    print("A1) Create User")
    print("A2) Allot Fare")
    print("A3) User delete")
    print("A4) Add a room")
    print("A5) See the fares of all rooms")
    print("A6) Display All users")
    print("1) Create Booking")
    print("2) Get Bill of a Customer")
    print("3) Get All Customers")
    print("4) Update Stay")
    print("5) Get Booking for a day")
    print("6) Get Bookings between two dates")
    print("7) Cancel Booking")
    print("8) Booking Counts")
    print("9) Occupancy")
    print("10) Summary")
    print("11) Payment Check")
    print("12) Update Paid Amount")
    print("13) Change User / Exit")
    print("=============================================================")
    try:
        choice = str(input("Enter your choice: "))
        print("=============================================================")
        return choice

    except ValueError as e:
        print(Fore.RED + "Invalid input. Please enter an integer.")
        print(Style.RESET_ALL, end="")
        print("=============================================================")
        return AdminMenu()


def FrontEndMenu():
    """
    Display a menu of options and prompt the user to choose one.

    Returns:
        int: The user's choice as an integer.

    Raises:
        ValueError: If the user's input is not a valid integer.
    """
    print("---------------------HOTEL SHAHI RAJDARBAR---------------------")
    print("1) Create Booking")
    print("2) Get Bill of a Customer")
    print("3) Get All Customers")
    print("4) Update Stay")
    print("5) Get Booking for a day")
    print("6) Get Bookings between two dates")
    print("7) Cancel Booking")
    print("8) Booking Counts")
    print("9) Occupancy")
    print("10) Summary")
    print("11) Payment Check")
    print("12) Update Paid Amount")
    print("13) Change User / Exit")
    print("=============================================================")
    try:
        choice = str(input("Enter your choice: "))
        print("=============================================================")
        return choice

    except ValueError as e:
        print(Fore.RED + "Invalid input. Please enter an integer.")
        print(Style.RESET_ALL, end="")
        print("=============================================================")
        return FrontEndMenu()


if Admin(userID, passwd):
    try:
        while True:
            choice = AdminMenu()
            if choice == "1":
                createBooking()
                c_id += 1
                book_id += 1
                input("Press any key to continue...")
                os.system("cls")
            elif choice == "2":
                try:
                    customer_id = int(input("Enter Customer Id: "))
                    bug_temp_get_bill(customer_id)
                except:
                    print(Fore.RED + "Maybe Invalid Input choices")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "3":
                getAllCustomers()
                input("Press any key to continue...")
                os.system("cls")
            elif choice == "4":
                try:
                    c_id = int(input("Enter customer ID: "))
                    newDate = str(input("Enter new date: "))
                    updateStay(c_id, newDate)
                except TypeError:
                    print(Fore.RED + "Might be that the User ID is wrong")
                    print(Style.RESET_ALL, end="")
                except InvalidCustomer:
                    print(Fore.RED + "Invalid customer ID - Check the username")
                    print(Style.RESET_ALL, end="")
                input("Press any key to continue...")
                os.system("cls")
            elif choice == "5":
                try:
                    date = str(input(Fore.BLUE + "Enter date: "))
                    print(Style.RESET_ALL, end="")
                    getBookingForDay(date)
                except:
                    print(Fore.RED + "Maybe Invalid Input choices")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "6":
                try:
                    start_date = str(input(Fore.BLUE + "Enter start date: "))
                    if start_date == "!END":
                        print(Style.RESET_ALL, end="")
                        continue
                    end_date = str(input("Enter end date: "))
                    if end_date == "!END":
                        print(Style.RESET_ALL, end="")
                        continue
                    print(Style.RESET_ALL, end="")
                    getBookingBetweenDays(start_date, end_date)
                except:
                    print(Fore.RED + "Maybe Invalid Input choices")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "7":
                deleteCustomerByID()
                input("Press any key to continue...")
                os.system("cls")
            elif choice == "8":
                try:
                    start_date = str(input(Fore.BLUE + "Enter start date: "))
                    end_date = str(input("Enter end date: "))
                    print(Style.RESET_ALL, end="")
                    print(get_booking_counts(start_date, end_date))
                except:
                    print(Fore.RED + "Maybe Invalid Input choices")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "9":
                try:
                    date = str(input("Enter date (YYYY-MM-DD): "))
                    if right_date(date):
                        print(occupancy(date))
                    else:
                        print(Fore.RED + "Invalid date")
                        print(Style.RESET_ALL, end="")
                except:
                    print(Fore.RED + "Maybe Invalid Input choices")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "10":
                try:
                    date = input(
                        "Enter date you want to get summary(YYYY-MM-DD) or enter 'c' or 'C' if you want of get summary of current date : "
                    )
                    if date == "c" or date == "C":
                        summary()
                    else:
                        summary(date)
                except:
                    print(Fore.RED + "Maybe Wrong input values")
                    print(Style.RESET_ALL, end='')
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "11":
                try:
                    customer = int(input("Enter Customer Id: "))
                    try:
                        payment_check(customer)
                    except:
                        print(Fore.RED + "Wrong Customer ID" + Style.RESET_ALL)
                except ValueError:
                    print(Fore.RED + "Might be that the User ID is wrong")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "12":
                try:
                    cust = int(input("Enter the Customer Id: "))
                    amt = int(input("Enter the amount paid: "))
                    update_bill(cust, amt)
                except TypeError:
                    print(Fore.RED + "Might be that the User ID is wrong")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "13":
                print(Fore.GREEN + "Exiting program...")
                k = input("Press any key to change user, type 'exit' to exit...")
                if k == "":
                    os.system("cls")
                    os.system("C:/Users/Lenovo/AppData/Local/Programs/Python/Python310/python.exe main.py")
                    print(Style.RESET_ALL, end='')
                else:
                    input("Exit done, you can leave")
                    os.system("cls")
                    print(Style.RESET_ALL, end="")
                    break
            elif choice == "A1":
                try:
                    user_id = str(input("Enter User ID: "))
                    pass_id = str(input("Enter Password: "))
                    if user_id == "" or pass_id == "":
                        print(Fore.YELLOW + "Enter atleast something")
                        print(Style.RESET_ALL, end='')
                    else:
                        CreateUser(user_id, pass_id)
                except:
                    print(Fore.RED + "Maybe Invalid Input choices")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "A2":
                allot_fare()
                input("Press any key to continue...")
                os.system("cls")
            elif choice == "A3":
                try:
                    user_id = str(input("Enter User ID: "))
                    DeleteUser(user_id)
                except:
                    print(Fore.RED + "Maybe Invalid Input choices")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "A4":
                add_room()
                input("Press any key to continue...")
                os.system("cls")
            elif choice == "A5":
                get_tariff_for_all_rooms()
            elif choice == "A6":
                DisplayUsers()
                input("Press any key to continue...")
                os.system("cls")
            else:
                print("Invalid choice")
                input("Press any key to continue...")
                os.system("cls")
    # except TypeError as e:
    #     print(Fore.RED + "An error occured when opening database")
    except NameError as e:
        print(
            Fore.RED + "Check, there's some value that is'nt defined or not defined properly"
        )
    except KeyboardInterrupt:
        print(Fore.RED + "\nProgram interrupted by user")

    finally:
        print(Style.RESET_ALL, end="")

elif AuthenticateUser(userID, passwd) and not Admin(userID, passwd):
    try:
        while True:
            choice = FrontEndMenu()
            if choice == "1":
                createBooking()
                c_id += 1
                book_id += 1
                input("Press any key to continue...")
                os.system("cls")
            elif choice == "2":
                try:
                    customer_id = int(input("Enter Customer Id: "))
                    bug_temp_get_bill(customer_id)
                except:
                    print(Fore.RED + "Maybe Invalid Input choices")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "3":
                getAllCustomers()
                input("Press any key to continue...")
                os.system("cls")
            elif choice == "4":
                try:
                    c_id = int(input("Enter customer ID: "))
                    newDate = str(input("Enter new date: "))
                    updateStay(c_id, newDate)
                except TypeError:
                    print(Fore.RED + "Might be that the User ID is wrong")
                    print(Style.RESET_ALL, end="")
                except InvalidCustomer:
                    print(Fore.RED + "Invalid customer ID - Check the username")
                    print(Style.RESET_ALL, end="")
                input("Press any key to continue...")
                os.system("cls")
            elif choice == "5":
                try:
                    date = str(input(Fore.BLUE + "Enter date: "))
                    print(Style.RESET_ALL, end="")
                    getBookingForDay(date)
                except:
                    print(Fore.RED + "Maybe Invalid Input choices")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "6":
                try:
                    start_date = str(input(Fore.BLUE + "Enter start date: "))
                    if start_date == "!END":
                        print(Style.RESET_ALL, end="")
                        continue
                    end_date = str(input("Enter end date: "))
                    if end_date == "!END":
                        print(Style.RESET_ALL, end="")
                        continue
                    print(Style.RESET_ALL, end="")
                    getBookingBetweenDays(start_date, end_date)
                except:
                    print(Fore.RED + "Maybe Invalid Input choices")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "7":
                deleteCustomerByID()
                input("Press any key to continue...")
                os.system("cls")
            elif choice == "8":
                try:
                    start_date = str(input(Fore.BLUE + "Enter start date: "))
                    end_date = str(input("Enter end date: "))
                    print(Style.RESET_ALL, end="")
                    print(get_booking_counts(start_date, end_date))
                except:
                    print(Fore.RED + "Maybe Invalid Input choices")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "9":
                try:
                    date = str(input("Enter date (YYYY-MM-DD): "))
                    if right_date(date):
                        print(occupancy(date))
                    else:
                        print(Fore.RED + "Invalid date")
                        print(Style.RESET_ALL, end="")
                except:
                    print(Fore.RED + "Maybe Invalid Input choices")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "10":
                try:
                    date = input(
                        "Enter date you want to get summary(YYYY-MM-DD) or enter 'c' or 'C' if you want of get summary of current date : "
                    )
                    if date == "c" or date == "C":
                        summary()
                    else:
                        summary(date)
                except:
                    print(Fore.RED + "Maybe Wrong input values")
                    print(Style.RESET_ALL, end='')
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "11":
                try:
                    customer = int(input("Enter Customer Id: "))
                    payment_check(customer)
                except ValueError:
                    print(Fore.RED + "Might be that the User ID is wrong")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "12":
                try:
                    cust = int(input("Enter the Customer Id: "))
                    amt = int(input("Enter the amount paid: "))
                    update_bill(cust, amt)
                except TypeError:
                    print(Fore.RED + "Might be that the User ID is wrong")
                    print(Style.RESET_ALL, end="")
                finally:
                    input("Press any key to continue...")
                    os.system("cls")
            elif choice == "13":
                print(Fore.GREEN + "Exiting program...")
                k = input("Press any key to change user, type 'exit' to exit...")
                if k == "":
                    os.system("cls")
                    os.system("C:/Users/Lenovo/AppData/Local/Programs/Python/Python310/python.exe main.py")
                    print(Style.RESET_ALL, end='')
                else:
                    input("Exit done, you can leave")
                    os.system("cls")
                    print(Style.RESET_ALL, end="")
                    break
            else:
                print("Invalid choice")
    except TypeError as e:
        print(Fore.RED + "An error occured when opening database")
    except NameError as e:
        print(
            Fore.RED + "Conenction wouldn't be created with wrong password or username"
        )
    except KeyboardInterrupt:
        print(Fore.RED + "\nProgram interrupted by user")

    finally:
        print(Style.RESET_ALL, end="")
