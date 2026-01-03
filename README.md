# Hotel Management System

A comprehensive Command Line Interface (CLI) based Hotel Management System written in Python. This application facilitates the management of hotel bookings, customers, rooms, and billing with a connection to a MySQL database.

## Features

### User Management
- **Authentication:** Secure login system for Admin and Staff users.
- **User Roles:**
    - **Admin:** Full access including user creation/deletion, room management, and fare adjustments.
    - **Staff (Front End):** Access to booking, billing, and customer management features.
- **Local Storage:** User credentials (excluding the hardcoded Admin) are stored locally in `users.been` using Python's `pickle` module.
- **Session Timer:** Includes a login session countdown.

### Booking & Reservations
- **Create Booking:** Streamlined process to book rooms, capturing guest details (Name, Address, Age, Gender).
- **Availability Check:** Automatically checks for room availability based on dates and room type (Normal 'np' / Super 's').
- **Cancel Booking:** Allows cancellation with logic for refund/charges based on check-in dates (e.g., 30% charge if cancelled after check-in).
- **View Bookings:** Retrieve bookings for a specific day or a date range.

### Room & Tariff Management
- **Add Rooms:** Admin can add new rooms to the inventory.
- **Fare Management:** Update tariffs for specific rooms or room types.
- **Room Types:** Supports different categories.

### Billing & Finance
- **Bill Calculation:** Automated bill generation including room tariff, service charges, and discounts. Handles tariff changes during a stay.
- **GST Calculation:** Dynamic GST application based on the total bill amount (>7500 implies 18%, else 12%).
- **Payment Tracking:** Update paid amounts and check payment status (Fully Paid/Pending).
- **Daily Summary:** View daily statistics on check-ins, check-outs, total revenue, and collected revenue.

### Reporting
- **Occupancy:** Check room occupancy for specific dates.
- **Booking Counts:** Analyze booking volume over a period.
- **Customer List:** View all customers and their billing status.

## Prerequisites

- Python 3.x
- MySQL Server

### Python Libraries
Install the required dependencies using pip:
```bash
pip install mysql-connector-python colorama
```

## Database Setup

The application requires a MySQL database named `hotel`. Ensure the following tables/views exist (inferred from code):
- `customer`: Stores guest details.
- `booking`: Stores booking links between guests and rooms.
- `room`: Stores room inventory and tariffs.
- `bill`: Stores billing information.
- `av_room`: View or table used to check room availability.

*Note: You may need to adjust the database connection parameters in `main.py`:*
```python
conn = sql.connect(
    host="localhost",
    user="DakshSingh",      # Change to your MySQL username
    password="dakshsingh",  # Change to your MySQL password
    database="hotel",
)
```

## Usage

1. **Start the Application:**
   Run the main script:
   ```bash
   python main.py
   ```

2. **Login:**
   - Default Admin Credentials:
     - User: `DakshSingh`
     - Password: `dakshsingh`
   - You can create new users via the Admin menu.

3. **Navigation:**
   - Follow the on-screen numbered menu to access different features.
   - Use `!END` in input prompts to exit specific operations.

## Important Notes

- **Hardcoded Paths:** The script contains a hardcoded path for restarting the application in `main.py`. You should update this to match your Python installation path if the restart feature fails.
- **Date Formats:** The system generally expects dates in `YYYY-MM-DD` format.