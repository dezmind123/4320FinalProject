import sqlite3
import os
from flask import Flask, render_template, request, flash, redirect, url_for

# Initialize Flask app
app = Flask(__name__)
app.config["DEBUG"] = True
app.config['SECRET_KEY'] = "unique_secret_key"

# Function to establish database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to initialize the database using schema.sql
def initialize_database():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.close()
        print("Database initialized using schema.sql.")

# Function to fetch admin credentials
def validate_admin(username, password):
    conn = get_db_connection()
    admin = conn.execute(
        'SELECT * FROM admins WHERE username = ? AND password = ?',
        (username, password)
    ).fetchone()
    conn.close()
    return admin

# Function to calculate total sales
def calculate_total_sales():
    cost_matrix = [[100, 75, 50, 100] for _ in range(12)]
    conn = get_db_connection()
    reservations = conn.execute('SELECT seatRow, seatColumn FROM reservations').fetchall()
    conn.close()
    total_sales = sum(cost_matrix[row['seatRow']][row['seatColumn']] for row in reservations)
    return total_sales

# Route: Homepage
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_option = request.form['option']
        if selected_option == 'admin':
            return redirect(url_for('admin'))
        elif selected_option == 'reserve':
            return redirect(url_for('reserve'))
    return render_template("index.html")

# Route: Admin login
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if validate_admin(username, password):
            return redirect(url_for('admin_portal'))
        else:
            flash('Login failed! Invalid credentials.')
    return render_template('admin.html')

# Route: Admin portal
@app.route('/admin_portal')
def admin_portal():
    conn = get_db_connection()
    reservations = conn.execute('SELECT * FROM reservations').fetchall()
    conn.close()
    seating_chart = [[None for _ in range(4)] for _ in range(12)]
    for res in reservations:
        seating_chart[res['seatRow']][res['seatColumn']] = res['passengerName']
    total_sales = calculate_total_sales()
    return render_template('admin_portal.html', seating_chart=seating_chart, total_sales=total_sales)

# Route: Reserve a seat
@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    conn = get_db_connection()
    reservations = conn.execute('SELECT * FROM reservations').fetchall()
    seating_chart = [[None for _ in range(4)] for _ in range(12)]
    for res in reservations:
        seating_chart[res['seatRow']][res['seatColumn']] = "X"
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        seat_row = int(request.form['seat_row']) - 1
        seat_col = int(request.form['seat_column']) - 1
        if seating_chart[seat_row][seat_col] == "X":
            flash("Seat is already reserved!")
        else:
            e_ticket = f"{first_name[0]}{last_name[0]}{seat_row}{seat_col}ET"
            conn.execute(
                'INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber) VALUES (?, ?, ?, ?)',
                (f"{first_name} {last_name}", seat_row, seat_col, e_ticket)
            )
            conn.commit()
            flash(f"Reservation successful! Your e-ticket number is {e_ticket}")
    conn.close()
    return render_template('reserve.html', seating_chart=seating_chart)

# Run the app
if __name__ == '__main__':
    initialize_database()
    app.run(port=5000)

