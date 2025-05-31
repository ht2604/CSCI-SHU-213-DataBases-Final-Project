from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql
from dateutil.relativedelta import relativedelta
import hashlib
import matplotlib as plt
plt.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import datetime, timedelta
from functools import wraps
from decimal import Decimal


conn = pymysql.connect(host='localhost',
                               port=3306,
                               user='root',
                               password='',
                               database='onlineairticketreservationsystem')

app = Flask(__name__)
app.secret_key = 'T2hfi4sdk9eey3ubw8ial1lcn6edv2ear7kfn6ocw43e7d98bdb8e'
#app.secret_key = 'secret key'#need a secret key for session management

# ========== Connecting to database==========
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='your_user',
        password='your_password',
        database='air_ticket_system',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
#========== Helper function for making bar plot
#Helper function for making pie plot
def make_autopct(values):
    def my_autopct(pct):
        total = sum(values)
        val = int(round(pct*total/100.0))
        # the number and ratio for the pie chart
        return '{p:.2f}%  ({v:d})'.format(p=pct,v=val)
    return my_autopct

#making the pie chart plot
def make_pie(username, index, value):
    plt.figure(figsize=(7,6.5))
    plt.pie(value, labels=index, autopct=make_autopct(value))
    plt.title("Pie: Your Spending in the Last 6 Months")
    plt.legend(loc='upper left')
    output_path = './templates/pic/'+username+'_pie.png'
    plt.savefig(output_path)
    return output_path

#making the bar chart plot
def make_bar(username, index, value):
    plt.figure(figsize=(7,6.5))
    plt.bar(index, height=value)
    plt.title("Bar: Your Spending in the Last 6 Months")
    plt.ylabel("Spending")
    plt.xlabel("Month")
    output_path = './templates/pic/'+username+'_bar.png'
    plt.savefig(output_path)
    return output_path

# ========== initial page that allows general research ==========
@app.route('/')
def index():
    return render_template('index.html')  # Need to define an index.html

# ========== General filght Search ==========
@app.route('/flight_search', methods=['GET', 'POST'])
def flight_search():
    cursor = conn.cursor()

    # 获取所有到达机场
    query = "SELECT DISTINCT arrival_airport FROM flight"
    cursor.execute(query)
    arrival_airport = cursor.fetchall()

    # 获取所有出发机场
    query = "SELECT DISTINCT departure_airport FROM flight"
    cursor.execute(query)
    departure_airport = cursor.fetchall()

    # 获取所有到达城市
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT arrival_airport FROM flight)"
    cursor.execute(query)
    arrival_city = cursor.fetchall()

    # 获取所有出发城市
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT departure_airport FROM flight)"
    cursor.execute(query)
    departure_city = cursor.fetchall()

    # 如果是 GET 请求，只用来获取数据，渲染搜索页面
    if request.method == 'GET':
        # 获取所有航班
        query = "SELECT * FROM flight"
        cursor.execute(query)
        search = cursor.fetchall()
        cursor.close()

        # 处理查询结果
        flights = [
            {
                'flight_number': flight[1],  # EX864
                'source': flight[2],         # 出发机场 (JFK)
                'destination': flight[4],    # 到达机场 (CDG)
                'departure_time': flight[3],  # 保留完整的 datetime 对象
                'arrival_time': flight[5],    # 保留完整的 datetime 对象
                'status': flight[8],         # 状态 (upcoming)
                'date': flight[3].date(),  # 完整的 datetime 对象
            }
            for flight in search  # 处理查询结果
        ]

        # 渲染结果到HTML模板
        return render_template('flight_search.html', 
                               flights=flights,  # 传递字典形式的结果
                               departure_city=departure_city,
                               departure_airport=departure_airport,
                               arrival_city=arrival_city,
                               arrival_airport=arrival_airport,
                               flight_date=None)  # flight_date 设置为 None
    # 如果是 POST 请求，需要发送数据到服务器，进行搜索
    elif request.method == 'POST':
        # 获取用户提交的搜索条件
        departure_city = request.form['departure_city']
        departure_airport = request.form['departure_airport']
        arrival_city = request.form['arrival_city']
        arrival_airport = request.form['arrival_airport']
        flight_date = request.form['flight_date']  # 获取用户选择的 flight_date
        
        # 判断是否选择了具体的搜索条件
        flag1 = bool(departure_city != "all")
        flag2 = bool(departure_airport != "all")
        flag3 = bool(arrival_city != "all")
        flag4 = bool(arrival_airport != "all")
        flag5 = bool(flight_date != "")  # 确保用户选择了日期
        
        # 如果没有选择任何搜索条件，给出错误提示
        if not (flag1 or flag2 or flag3 or flag4 or flag5):
            error = "At least 1 field should be specified!"
            return render_template('flight_search.html', 
                                   departure_city=departure_city,
                                   departure_airport=departure_airport,
                                   arrival_city=arrival_city,
                                   arrival_airport=arrival_airport,
                                   error=error,
                                   flight_date=flight_date)  # 传递 flight_date 给模板

        # 动态构建 SQL 查询条件
        conditions = []
        
        if flag1:
            conditions.append(f"departure_airport IN (SELECT airport_name FROM airport WHERE airport_city = \"{departure_city}\")")
        if flag2:
            conditions.append(f"departure_airport = \"{departure_airport}\"")
        if flag3:
            conditions.append(f"arrival_airport IN (SELECT airport_name FROM airport WHERE airport_city = \"{arrival_city}\")")
        if flag4:
            conditions.append(f"arrival_airport = \"{arrival_airport}\"")
        if flag5:
            # 只取日期部分进行比较
            conditions.append(f"DATE(departure_time) = \"{flight_date}\"")
        
        #合并所有条件并拼接查询
        query = "SELECT * FROM flight WHERE " + " AND ".join(conditions) + " AND status = 'Upcoming' "


        print(f"Executing query: {query}")  # Debug 输出
        # 执行查询
        cursor.execute(query)
        search = cursor.fetchall()
        print("Query result:", search)
        cursor.close()

        
        
        # 渲染查询结果页面并传递搜索结果
        flights = [
        {
            'flight_number': flight[1],  # EX864
            'source': flight[2],         # 出发机场 (JFK)
            'destination': flight[4],    # 到达机场 (CDG)
            'departure_time': flight[3],  # 保留完整的 datetime 对象
            'arrival_time': flight[5],    # 保留完整的 datetime 对象
            'status': flight[7],         # 状态 (upcoming)
            'date': flight[3],  # 完整的 datetime 对象
        }
        for flight in search  # 处理查询结果
    ]

    # 渲染结果到HTML模板
    return render_template('flight_search.html', 
                        flights=flights,  # 传递字典形式的结果
                        departure_city=departure_city,
                        departure_airport=departure_airport,
                        arrival_city=arrival_city,
                        arrival_airport=arrival_airport,
                        flight_date=flight_date)



# ========== General flight status check  ==========
@app.route('/flight_status', methods=['GET', 'POST'])
def flight_status():
    if request.method == 'POST':
        # 获取表单字段
        flight_number = request.form['flight_number']
        arrival_date = request.form['arrival_date']
        departure_date = request.form['departure_date']
        
        # 检查是否至少填写了一个字段
        if not (flight_number or arrival_date or departure_date):
            error = "At least 1 field should be specified!"
            return render_template('flight_status.html', error=error)
        
        # 设置查询条件
        flag1 = bool(flight_number)
        flag2 = bool(arrival_date)
        flag3 = bool(departure_date)
        
        sub1 = " flight_num = \'{}\' ".format(flight_number) if flag1 else ""
        sub2 = " DATE(arrival_time) = DATE(\'{}\') ".format(arrival_date) if flag2 else ""
        sub3 = " DATE(departure_time) = DATE(\'{}\') ".format(departure_date) if flag3 else ""
        
        # 合并所有的查询条件
        merged_sub = list(filter(None, [sub1, sub2, sub3]))
        query = "SELECT airline_name, flight_num, departure_time, arrival_time, status FROM flight WHERE " + " AND ".join(merged_sub)
        print("this is query:", query)  # Debug 输出
        # 执行查询
        cursor = conn.cursor()
        cursor.execute(query)
        status = cursor.fetchall()
        print("Query result:", status)
        cursor.close()
        
        # 返回查询结果页面
        flight_status = []
        for row in status:
            flight = {
                'airline_name': row[0],
                'flight_number': row[1],
                'departure_time': row[2],
                'arrival_time': row[3],
                'status': row[4]
            }
            flight_status.append(flight)

        # 返回查询结果页面
        return render_template('flight_status.html', flight_status=flight_status)
    
    # 如果是 GET 请求，直接返回表单页面
    return render_template('flight_status.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 获取表单数据
        role = request.form.get('identity')
        # 根据角色选择获取哪个字段
        if role == 'AirlineStaff':
            print("Airline Staff login")
            username = request.form.get('username')
        else:
            username = request.form.get('email')
            print(f"Username: {username}")  # Debug 输出
        # username = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('identity')
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        if role == 'Customer':
            query = "SELECT * FROM customer WHERE email = %s AND password = MD5(%s)"
            cursor.execute(query, (username, password))
            data = cursor.fetchone()
            
            if data:
                session['username'] = username
                session['identity'] = role
                session['name'] = data['name']
                cursor.close()
                # 登录成功后，重定向去 /customer/home
                return redirect(url_for('customer_home'))  
            else:
                cursor.close()
                error = 'Invalid credentials'
                return render_template('login.html', error=error)
    
        elif role == 'BookingAgent':
            query = "SELECT * FROM booking_agent WHERE email = %s AND password = MD5(%s)"
            cursor.execute(query, (username, password))
            data = cursor.fetchone()
            if data:
                session['username'] = username
                session['identity'] = role
                session['name'] = username  # Booking Agent 没有 name 字段就显示邮箱
                cursor.close()
                return redirect(url_for('agent_home'))
            else:
                cursor.close()
                error = 'Invalid credentials'
                return render_template('login.html', error=error)
    

        elif role == 'AirlineStaff':
            
            query = "SELECT * FROM  permission  natural join  airline_staff WHERE username = %s AND password = MD5(%s)"
            
            cursor.execute(query, (username, password))
            data = cursor.fetchone()
            if data:
                print('session:',session)
                session['username'] = username
                session['identity'] = role
                session['name'] = username  # Airline Staff 用 username
                session['permissions'] = data['permission_type']  
                session['airline'] = data['airline_name']  # Airline Staff 的 airline
                print("find this staff")
                cursor.close()
                return redirect(url_for('staff_home'))
            else:
                print
                cursor.close()
                print("not working")
                error = 'Invalid credentials'
                return render_template('login.html', error=error)
    

        # 登录失败
        cursor.close()
        flash('Invalid user_name or password', 'error')
        return redirect(url_for('login'))

    # GET 请求直接渲染登录页面
    return render_template('login.html')


# ========== register ==========
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        # 如果是GET请求，获取航空公司列表供工作人员注册使用
        cursor = conn.cursor()
        query = "SELECT DISTINCT * FROM airline"
        cursor.execute(query)
        airline_list = cursor.fetchall()
        cursor.close()
        return render_template('register.html', airline_list=airline_list)
    
    # POST请求处理
    identity = request.form.get('identity')
    
    if not identity:
        flash("Please select an identity", "error")
        return render_template('register.html')
    
    if identity == 'customer':
        # 客户注册处理
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        phone = request.form.get('phone')
        passport_number = request.form.get('passport_number')
        passport_expiry = request.form.get('passport_expiry')
        passport_country = request.form.get('passport_country')
        date_of_birth = request.form.get('date_of_birth')
        
        # 可选字段
        building_number = request.form.get('building_number', None)
        street = request.form.get('street', None)
        city = request.form.get('city', None)
        state = request.form.get('state', None)
        
        # 检查必填字段
        if not all([email, name, password, phone, passport_number, 
                   passport_expiry, passport_country, date_of_birth]):
            flash("Please fill in all required fields.", "error")
            return render_template('register.html')
            
        # 检查邮箱是否已存在
        cursor = conn.cursor()
        query = "SELECT * FROM customer WHERE email = %s"
        cursor.execute(query, (email,))
        if cursor.fetchone():
            cursor.close()
            flash("This email is already registered", "error")
            return render_template('register.html')
            
        # 插入新客户
        ins = """
        INSERT INTO customer (email, name, password, building_number, street, 
        city, state, phone_number, passport_number, passport_expiration, passport_country, date_of_birth,balance)
        VALUES (%s, %s, MD5(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s,30000)
        """
        cursor.execute(ins, (email, name, password, building_number, street, 
                           city, state, phone, passport_number, passport_expiry, 
                           passport_country, date_of_birth))
        conn.commit()
        cursor.close()
        flash("Customer registered successfully!", "success")
        return redirect(url_for('login'))
        
    elif identity == 'agent':
        # 代理注册处理
        email = request.form.get('agent_email')
        password = request.form.get('agent_password')
        # booking_agent_id = request.form.get('booking_agent_id')
        print('email:', email)
        print('password:', password)
        if not all([email, password]):
            flash("Please fill in all required fields.", "error")
            return render_template('register.html')
            
        # 检查邮箱是否已存在
        cursor = conn.cursor()
        query = "SELECT * FROM booking_agent WHERE email = %s"
        cursor.execute(query, (email,))
        if cursor.fetchone():
            cursor.close()
            flash("This email is already registered", "error")
            return render_template('register.html')
            
        # 生成新代理ID
        query = "SELECT MAX(booking_agent_id) FROM booking_agent"
        cursor.execute(query)
        max_id = cursor.fetchone()[0]
        agent_id = 1 if max_id is None else max_id + 1
        print('agent_id:', agent_id)
        
        # 插入新代理
        ins = "INSERT INTO booking_agent (email, password,booking_agent_id) VALUES (%s, MD5(%s), %s)"
        cursor.execute(ins, (email, password, agent_id))
        conn.commit()
        cursor.close()
        flash("Booking Agent registered successfully!", "success")
        return redirect(url_for('register'))
        
    elif identity == 'staff':
        # 工作人员注册处理
        email = request.form.get('username')
        password = request.form.get('staff_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        birthday = request.form.get('birthday')
        airline = request.form.get('airline')
        print('email:', email)
        print('password:', password)
        print('first_name:', first_name)
        print('last_name:', last_name)
        print('birthday:', birthday)
        print('airline:', airline)

        
        if not all([email, password, first_name, last_name, birthday, airline]):
            flash("Please fill in all required fields.", "error")
            return render_template('register.html')
            
        # 检查用户名是否已存在
        cursor = conn.cursor()
        query = "SELECT * FROM airline_staff WHERE username = %s"
        cursor.execute(query, (email,))
        if cursor.fetchone():
            cursor.close()
            flash("This username is already registered", "error")
            return render_template('register.html')
            
        # 插入新工作人员
        ins = """
        INSERT INTO airline_staff (username, password, first_name, last_name, date_of_birth, airline_name)
        VALUES (%s, MD5(%s), %s, %s, %s, %s)
        """
        cursor.execute(ins, (email, password, first_name, last_name, birthday, airline))
        conn.commit()
        cursor.close()
        flash("Airline Staff registered successfully!", "success")
        return redirect(url_for('login'))
        
    else:
        flash("Invalid identity selection", "error")
        return render_template('register.html')


# #####################Customer Begin########################################
#Customer Home page
@app.route('/customer/home', methods=['GET', 'POST'])
def customer_home():
    if 'username' not in session or session.get('identity') != 'Customer':
        print('User not logged in or not a customer')
        return redirect(url_for('login'))

    email = session["username"]
    cursor = conn.cursor()
    
    show_upcoming = request.args.get('show_upcoming', 'I just need the upcoming flight')  # 默认值为 'yes' 表示只显示未来航班
    #only future flight
    if show_upcoming == 'I just need the upcoming flight':
        query = """
            SELECT airline_name, flight_num, departure_airport, departure_time,
                   arrival_airport, arrival_time, price, status, ticket_id, purchase_date
            FROM flight 
            NATURAL JOIN ticket 
            NATURAL JOIN purchases
            WHERE customer_email = %s AND departure_time > NOW()     
            ORDER BY departure_time DESC;
        """
    else:
        # show all flight
        query = """
            SELECT airline_name, flight_num, departure_airport, departure_time,
                   arrival_airport, arrival_time, price, status, ticket_id, purchase_date
            FROM flight 
            NATURAL JOIN ticket 
            NATURAL JOIN purchases
            WHERE customer_email = %s
            ORDER BY departure_time DESC;
        """
    
    # print('Query:', query)  
    print(f"Executing query with email: {email}")
    print(f"Query: {query}")
    cursor.execute(query, (email,))
    purchased_flights = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
    print('Query Result:', purchased_flights)
    cursor.close()

    return render_template('customer_home.html', data=purchased_flights, show_upcoming=show_upcoming)




@app.route('/search_and_purchase', methods=['GET', 'POST'])
def search_and_purchase():
    email = session.get("username")
    cursor = conn.cursor()
    flights = []
    balance = None
    error = None

    # Get the user's balance
    cursor.execute('SELECT balance FROM customer WHERE email = %s', (email,))
    result = cursor.fetchone()
    if result:
        balance = result[0]

    if request.method == 'POST':
        action = request.form.get('action')  

        if action == 'search':
            print('start searching')
            departure_city = request.form.get('departure_city')
            departure_airport = request.form.get('departure_airport')
            arrival_city = request.form.get('arrival_city')
            arrival_airport = request.form.get('arrival_airport')
            flight_date = request.form.get('flight_date')

            now = datetime.now()
            min_departure_time = now + timedelta(hours=3)
            min_departure_time_str = min_departure_time.strftime('%Y-%m-%d %H:%M:%S')

            conditions = []
            params = []

            if departure_city and departure_city != "all":
                conditions.append("departure_airport IN (SELECT airport_name FROM airport WHERE airport_city = %s)")
                params.append(departure_city)
            if departure_airport and departure_airport != "all":
                conditions.append("departure_airport = %s")
                params.append(departure_airport)
            if arrival_city and arrival_city != "all":
                conditions.append("arrival_airport IN (SELECT airport_name FROM airport WHERE airport_city = %s)")
                params.append(arrival_city)
            if arrival_airport and arrival_airport != "all":
                conditions.append("arrival_airport = %s")
                params.append(arrival_airport)
            if flight_date:
                conditions.append("DATE(departure_time) = %s")
                params.append(flight_date)

            conditions.append("departure_time > %s")
            params.append(min_departure_time_str)

            where_clause = " AND ".join(conditions)
            query = f"SELECT * \
                        FROM flight JOIN airplane ON flight.airplane_id = airplane.airplane_id \
                        WHERE {where_clause}"

            print("执行的SQL:", query)
            print("参数：", params)

            cursor.execute(query, params)
            flights = cursor.fetchall()
            adjusted_flights = []
            for flight in flights:
                flight_id = flight[1]  # flight[1] 是 flight_id
                seat_num = flight[11]  # flight[11] 是 airplane.seat_num

                cursor.execute("SELECT COUNT(*) FROM ticket WHERE flight_num = %s", (flight_id,))
                result = cursor.fetchone()
                sold_tickets = result[0] if result else 0

                remaining_seats = seat_num - sold_tickets
                if remaining_seats < 0:
                    remaining_seats = 0

                # 把 flight 转为 list，替换第 11 位，再转回 tuple
                flight = list(flight)
                flight[11] = remaining_seats
                adjusted_flights.append(tuple(flight))

            flights = adjusted_flights
            print("查询结果:", flights)

            return render_template('customer_search_and_purchase.html', balance=balance, search_results=flights)

        elif action == 'purchase':
            print('start purchasing')
            airline_name = request.form.get('airline_name')
            flight_num = request.form.get('flight_num')

            try:
                # Check the price of the flight
                cursor.execute('SELECT price FROM flight WHERE airline_name = %s AND flight_num = %s', (airline_name, flight_num))
                flight = cursor.fetchone()

                if not flight:
                    error = "Flight not found."
                    print('error:', error)
                    return render_template('customer_search_and_purchase.html', balance=balance, error=error)

                price = flight[0]
                print("Flight price:", price)
                if balance < price:
                    error = "Insufficient balance."
                    return render_template('customer_search_and_purchase.html', balance=balance, error=error)
                else:
                    print("Balance is sufficient.")
                    # Check available seats for this flight
                    check_seats_query = """
                    SELECT 
                        airplane.seats - COUNT(ticket.customer_email) AS available_seats
                    FROM 
                        flight 
                    JOIN 
                        airplane ON flight.airplane_id = airplane.airplane_id
                    LEFT JOIN 
                        ticket ON ticket.flight_num = flight.flight_num AND ticket.airline_name = flight.airline_name
                    WHERE 
                        flight.airline_name = %s AND flight.flight_num = %s
                    GROUP BY 
                        airplane.seats;
                """
                    cursor.execute(check_seats_query, (airline_name, flight_num))
                    result = cursor.fetchone()
                    available_seats = result[0] if result else 0
                    print("Available seats:", available_seats)

                    if not result:
                        flash("Error: Flight not found.")
                        print("Error: Flight not found.")
                        return redirect(url_for('search_and_purchase'))

                    available_seats = result[0]
                    if available_seats <= 0:
                        print("No available seats.")
                        flash(f"Sorry, there are no available seats for flight \"{airline_name}-{flight_num}\".")
                        return render_template('customer_search_and_purchase.html', balance=balance, error="No available seats.")



                    # If the balance is sufficient, check if the user has already purchased this flight
                    cursor.execute('SELECT ticket_id FROM ticket WHERE customer_email = %s AND flight_num = %s', (email, flight_num))
                    existing_ticket = cursor.fetchone()
                    print("Existing ticket query result:", existing_ticket)
                    if existing_ticket and request.form.get('confirm') != 'yes':
                        # If the user has already purchased this flight, ask for confirmation to purchase again
                        flash('You already have a ticket for this flight. Do you want to purchase another one?')
                        return render_template('customer_confirm_purchase.html', airline_name=airline_name, flight_num=flight_num, price=price)
                    else:
                        #If the user has not purchased this flight, proceed with the purchase
                        print("Proceeding with purchase.")
                        new_balance = balance - price
                        print('1')
                        
                        cursor.execute('UPDATE customer SET balance = %s WHERE email = %s', (new_balance, email))
                        print('2')
                      
                        cursor.execute('SELECT MAX(ticket_id) FROM ticket WHERE flight_num = %s', (flight_num,))
                        print('3')
                        # answer = cursor.fetchone()
                        # print('answer:', answer)
                        
                        print('Inserting ticket record')
                        cursor.execute('INSERT INTO ticket (customer_email, airline_name, flight_num, booking_agent_email) VALUES (%s, %s, %s, NULL)',
                                    (email, airline_name, flight_num))

                        # 获取自动生成的 ticket_id
                        ticket_id = cursor.lastrowid
                        print('Auto-generated ticket_id:', ticket_id)
                        # Insert ticket record WITHOUT specifying ticket_id
                        cursor.execute('INSERT INTO ticket (customer_email, airline_name, flight_num, booking_agent_email) VALUES (%s, %s, %s, NULL)',
                                    (email, airline_name, flight_num))

                        # Get the auto-generated ticket_id
                        ticket_id = cursor.lastrowid
                        print('Auto-generated ticket_id:', ticket_id)

                        # Insert into purchases using the auto-generated ticket_id
                        # cursor.execute('INSERT INTO purchases (ticket_id, customer_email, booking_agent_id, purchase_date) VALUES (%s, %s, NULL, NOW())',
                        #             (ticket_id, email))

                        print("Purchase successful.")

                        # Updating Balance
                        balance = new_balance
                        print("Updated balance:", balance)
                        return redirect(url_for('search_and_purchase'))

            except Exception as e:
                conn.rollback()
                print("Purchase Error:", str(e))
                error = "An error occurred: " + str(e)
    return render_template('customer_search_and_purchase.html', balance=balance, error=error, search_results=flights)




    
# #Track spending
@app.route('/customer_spending')
def customer_spending():
    # 你的处理逻辑
    # if 'username' not in session or session.get('user_type') != 'customer':
    #     print
    #     print('User not logged in or not a customer')
    #     return redirect(url_for('login'))

    if 'username' not in session or session.get('identity') != 'Customer':
        print('User not logged in or not a customer')
        return redirect(url_for('login'))


    email = session["username"]
    cursor = conn.cursor()

    query = """
        SELECT price, ticket_id, purchase_date 
        FROM purchases 
        NATURAL JOIN ticket 
        NATURAL JOIN flight
        WHERE customer_email = %s
        ORDER BY purchase_date ASC;
    """
    cursor.execute(query, (email,))
    spending_data = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
    cursor.close()

    if not spending_data:
        months, spendings, now, past6m = False, False, False, False
    else:
        # 处理月份和花费
        months = []
        now = datetime.today().year * 100 + datetime.today().month
        t = spending_data[0]["purchase_date"].year * 100 + spending_data[0]["purchase_date"].month
        months.append(t)
        while t < now:
            if t % 100 == 12:
                t += 88
            t += 1
            months.append(t)
        spendings = [0 for _ in range(len(months))]
        for row in spending_data:
            price = row["price"]
            month = row["purchase_date"].year * 100 + row["purchase_date"].month
            if month in months:
                m = months.index(month)
                spendings[m] += float(price)
        now = str(datetime.today().year) + "-" + str(datetime.today().month)
        past_year = datetime.today().year
        past_month = datetime.today().month - 6
        if past_month < 1:
            past_month += 12
            past_year -= 1
        past6m = str(past_year) + "-" + str(past_month)
        if len(now) < 7:
            now = now[:5] + "0" + now[-1]
        if len(past6m) < 7:
            past6m = past6m[:5] + "0" + past6m[-1]

    return render_template('customer_spending.html',
                           months=months,
                           spendings=spendings,
                           now=now,
                           past6m=past6m)



# ####################Booking Agent Begin########################################

# ####################Booking Agent Begin########################################
# # Booking agent home page
@app.route('/agent/home', methods=['GET', 'POST'])
def agent_home():
    if 'username' not in session or session.get('identity') != 'BookingAgent':
        flash("You must be logged in as a booking agent.")
        return redirect(url_for('login'))

    agent_email = session['username']
    print('agent_email:', agent_email)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    print('SESSION内容:', dict(session))

    flights = []

    if request.method == 'POST':
        # 搜索条件
        flight_num = request.form.get('flight_num')
        departure_city = request.form.get('departure_city')
        arrival_city = request.form.get('arrival_city')
        departure_date = request.form.get('departure_date')
        show_type = request.form.get('show_type', 'upcoming')

        # 构造查询语句
        query = """
            SELECT flight.*, ticket.ticket_id, purchases.customer_email
            FROM flight
            JOIN ticket ON flight.flight_num = ticket.flight_num
            JOIN purchases ON ticket.ticket_id = purchases.ticket_id
            WHERE purchases.booking_agent_id = (
                SELECT booking_agent_id FROM booking_agent WHERE email = %s
            )
        """
        params = [agent_email]

        # 添加筛选条件
        # if show_type == 'upcoming':
        #     query += " AND flight.departure_time > NOW()"
        if show_type == 'upcoming':
            query += " AND flight.status = 'upcoming'"
        elif show_type == 'delayed':
            query += " AND flight.status = 'delayed'"
        if flight_num:
            query += " AND flight.flight_num = %s"
            params.append(flight_num)
        if departure_city:
            query += " AND flight.departure_airport IN (SELECT airport_name FROM airport WHERE airport_city = %s)"
            params.append(departure_city)
        if arrival_city:
            query += " AND flight.arrival_airport IN (SELECT airport_name FROM airport WHERE airport_city = %s)"
            params.append(arrival_city)
        if departure_date:
            query += " AND DATE(flight.departure_time) = %s"
            params.append(departure_date)

        query += " ORDER BY flight.departure_time ASC"

        cursor.execute(query, params)
        flights = cursor.fetchall()
        username=session.get('username')
       

    cursor.close()
    return render_template('agent_home.html', flights=flights, username=session.get('username'))

# # logout
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # 清除所有登录信息
    flash("You have been logged out.")
    return redirect(url_for('login'))


# #Purchase and search a ticket for a customer
@app.route('/agent/search_and_purchase', methods=['GET', 'POST'])
def agent_search_and_purchase():
    if 'username' not in session or session.get('identity') != 'BookingAgent':
        flash("You must be logged in as a booking agent.")
        return redirect(url_for('login'))

    agent_email = session['username']
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    search_results = []
    error = None
    flight=[]

    # 获取 agent 的 booking_agent_id
    cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE email = %s", (agent_email,))
    agent_id_result = cursor.fetchone()
    if not agent_id_result:
        flash("Booking agent not found in system.")
        return redirect(url_for('login'))
    agent_id = agent_id_result['booking_agent_id']

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'search':
            print("start searching")
            departure_city = request.form.get('departure_city')
            departure_airport = request.form.get('departure_airport')
            arrival_city = request.form.get('arrival_city')
            arrival_airport = request.form.get('arrival_airport')
            flight_date = request.form.get('flight_date')

            now = datetime.now()
            min_departure_time = now + timedelta(hours=3)
            min_departure_time_str = min_departure_time.strftime('%Y-%m-%d %H:%M:%S')

            conditions = ["departure_time > %s"]
            params = [min_departure_time_str]

            # conditions.append("airline_name IN (SELECT airline_name FROM booking_agent_work_for WHERE email = %s)")
            conditions.insert(0, "flight.airline_name IN (SELECT booking_agent_work_for.airline_name FROM booking_agent_work_for WHERE booking_agent_work_for.email = %s)")
            params.insert(0, agent_email)  # 插入在前面

            if departure_city:
                conditions.append("departure_airport IN (SELECT airport_name FROM airport WHERE airport_city = %s)")
                params.append(departure_city)
            if departure_airport:
                conditions.append("departure_airport = %s")
                params.append(departure_airport)
            if arrival_city:
                conditions.append("arrival_airport IN (SELECT airport_name FROM airport WHERE airport_city = %s)")
                params.append(arrival_city)
            if arrival_airport:
                conditions.append("arrival_airport = %s")
                params.append(arrival_airport)
            if flight_date:
                conditions.append("DATE(departure_time) = %s")
                params.append(flight_date)

            where_clause = " AND ".join(conditions)

            query = f"""
                SELECT * FROM flight 
                JOIN airplane ON flight.airplane_id = airplane.airplane_id
                WHERE {where_clause}
            """

            print("执行SQL:", query)
            print("参数：", params)

            cursor.execute(query, tuple(params))
            raw_flights = cursor.fetchall()

            adjusted_flights = []
            for flight in raw_flights:
                # flight = list(flight)
                flight_num = flight['flight_num']  # flight_num
                seat_num = int(flight['seats'])  # airplane.seats

                cursor.execute("SELECT COUNT(*) FROM ticket WHERE flight_num = %s", (flight_num,))
                result = cursor.fetchone()
                sold = result['COUNT(*)'] if result else 0
                remaining_seats = max(seat_num - sold, 0)

                flight['remaining_seats'] = remaining_seats  # 替换 seats 字段为剩余座位
                adjusted_flights.append(flight)

            print("最终航班结果：", adjusted_flights)

            return render_template('agent_search_and_purchase.html', flights=adjusted_flights)

        elif action == 'purchase':
            customer_email = request.form.get('customer_email')
            airline_name = request.form.get('airline_name')
            flight_num = request.form.get('flight_num')

            # 检查是否重复购票
            # cursor.execute("""SELECT * FROM ticket 
            #                   WHERE customer_email = %s AND flight_num = %s""", 
            #                (customer_email, flight_num))
            # 不在ticket table上添加customer_email和booking_agent_email，而是join ticket and purchase table
            cursor.execute("""
                SELECT *
                FROM purchases p
                JOIN ticket t ON p.ticket_id = t.ticket_id
                WHERE p.customer_email = %s AND t.flight_num = %s AND t.airline_name = %s
            """, (customer_email, flight_num, airline_name))
            if cursor.fetchone():
                flash("Customer already has a ticket for this flight.")
            else:
                # 检查是否有available seats
                cursor.execute("""
                    SELECT airplane.seats
                    FROM flight
                    JOIN airplane ON flight.airplane_id = airplane.airplane_id
                    WHERE flight.flight_num = %s AND flight.airline_name = %s
                """, (flight_num, airline_name))
                airplane_info = cursor.fetchone()
                if not airplane_info:
                    flash("Could not find airplane info.")
                    return redirect(url_for('agent_search_and_purchase'))
                total_seats = airplane_info['seats']

                cursor.execute("""
                    SELECT COUNT(*) AS sold
                    FROM ticket
                    WHERE flight_num = %s AND airline_name = %s
                """, (flight_num, airline_name))
                sold_info = cursor.fetchone()
                sold = sold_info['sold'] if sold_info else 0

                remaining_seats = max(total_seats - sold, 0)
                # flight['remaining_seats'] = remaining_seats

                if remaining_seats <= 0:
                    flash("No available seats for this flight.")
                    return redirect(url_for('agent_search_and_purchase'))
                
                # 获取航班价格
                cursor.execute("""
                    SELECT price FROM flight 
                    WHERE flight_num = %s AND airline_name = %s
                """, (flight_num, airline_name))
                flight_info = cursor.fetchone()
                if not flight_info:
                    flash("Flight not found.")
                    return redirect(url_for('agent_search_and_purchase'))

                price = flight_info['price']

                # 获取customer余额
                cursor.execute("""
                    SELECT balance FROM customer WHERE email = %s
                """, (customer_email,))
                customer_info = cursor.fetchone()
                if not customer_info:
                    flash("Customer not found.")
                    return redirect(url_for('agent_search_and_purchase'))

                balance = customer_info['balance']

                if balance < price * Decimal('1.1'):
                    flash("Insufficient balance. Purchase failed.")
                    return redirect(url_for('agent_search_and_purchase'))
                
                # 创建新的ticket记录，即新的ticket_id
                cursor.execute("SELECT MAX(ticket_id) FROM ticket")
                max_id = cursor.fetchone()['MAX(ticket_id)']
                ticket_id = 1 if max_id is None else max_id + 1

                # 插入 ticket   
                cursor.execute("""INSERT INTO ticket (ticket_id, airline_name, flight_num,customer_email,booking_agent_email) 
                                  VALUES (%s, %s, %s,%s,%s)""", 
                               (ticket_id, airline_name, flight_num, customer_email, agent_email))

                # 插入 purchases
                cursor.execute("""INSERT INTO purchases (ticket_id, customer_email, booking_agent_id, purchase_date)
                                  VALUES (%s, %s, %s, NOW())""", 
                               (ticket_id, customer_email, agent_id))
                
                # 扣除余额
                cursor.execute("""
                    UPDATE customer SET balance = balance - %s WHERE email = %s
                """, (price * Decimal('1.1'), customer_email))

                conn.commit()
                flash("Ticket successfully purchased for customer.")

    cursor.close()
    return render_template('agent_search_and_purchase.html', flights=search_results)


@app.route('/agent/commission', methods=['GET', 'POST'])
def agent_commission():
    if 'username' not in session or session.get('identity') != 'BookingAgent':
        flash("You must be logged in as a booking agent.")
        return redirect(url_for('login'))

    agent_email = session['username']
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 获取 agent id
    cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE email = %s", (agent_email,))
    agent_row = cursor.fetchone()
    if not agent_row:
        flash("Booking agent ID not found.")
        return redirect(url_for('login'))
    agent_id = agent_row['booking_agent_id']
    print("Booking agent ID:", agent_id)
    print("Booking agent email:", agent_email)

    # 默认时间范围为过去 30 天
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=30)

    # 如果用户通过 POST 提交了日期，则使用用户输入的日期
    if request.method == 'POST':
        user_start = request.form.get('start_date')
        user_end = request.form.get('end_date')
        if user_start and user_end:
            try:
                start_date = datetime.strptime(user_start, "%Y-%m-%d").date()
                end_date = datetime.strptime(user_end, "%Y-%m-%d").date()
            except:
                flash("Invalid date format.")

    # 如果没有用户提供日期，则查询所有时间的记录
    if not request.form.get('start_date') and not request.form.get('end_date'):
        query = """
            SELECT price
            FROM purchases
            JOIN ticket ON purchases.ticket_id = ticket.ticket_id
            JOIN flight ON ticket.flight_num = flight.flight_num AND ticket.airline_name = flight.airline_name
            WHERE purchases.booking_agent_id = %s
        """
        cursor.execute(query, (agent_id,))
    else:
        # 查询票价总和，默认查询过去 30 天的记录，或者用户选择的时间范围
        query = """
            SELECT price
            FROM purchases
            JOIN ticket ON purchases.ticket_id = ticket.ticket_id
            JOIN flight ON ticket.flight_num = flight.flight_num AND ticket.airline_name = flight.airline_name
            WHERE purchases.booking_agent_id = %s
            AND DATE(purchase_date) BETWEEN %s AND %s
        """
        cursor.execute(query, (agent_id, start_date, end_date))

    rows = cursor.fetchall()
    print("查询结果:", rows)
    cursor.close()

    total_tickets = len(rows)
    total_commission = sum([float(r['price']) * 0.1 for r in rows])
    avg_commission = total_commission / total_tickets if total_tickets > 0 else 0.0

    return render_template("agent_commission.html",
                           total_commission=round(total_commission, 2),
                           avg_commission=round(avg_commission, 2),
                           total_tickets=total_tickets,
                           start_date=start_date,
                           end_date=end_date)


# #Top customers based on number of tickets sold and amount of commission
@app.route('/agent/top_customers')
def agent_top_customers():
    if 'username' not in session or session.get('identity') != 'BookingAgent':
        flash("You must be logged in as a booking agent.")
        return redirect(url_for('login'))

    agent_email = session['username']
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 获取 booking_agent_id
    cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE email = %s", (agent_email,))
    row = cursor.fetchone()
    if not row:
        flash("Booking agent not found.")
        return redirect(url_for('login'))
    agent_id = row['booking_agent_id']

    # 过去 6 个月：购票数量前 5
    cursor.execute("""
        SELECT customer_email, COUNT(*) AS ticket_count
        FROM purchases
        WHERE booking_agent_id = %s
        AND purchase_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY customer_email
        ORDER BY ticket_count DESC
        LIMIT 5
    """, (agent_id,))
    top_ticket_customers = cursor.fetchall()

    # 过去 1 年：佣金最高前 5
    cursor.execute("""
        SELECT p.customer_email, SUM(f.price * 0.1) AS total_commission
        FROM purchases p
        JOIN ticket t ON p.ticket_id = t.ticket_id
        JOIN flight f ON t.flight_num = f.flight_num AND t.airline_name = f.airline_name
        WHERE p.booking_agent_id = %s
        AND p.purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY p.customer_email
        ORDER BY total_commission DESC
        LIMIT 5
    """, (agent_id,))
    top_commission_customers = cursor.fetchall()

    cursor.close()
    return render_template('agent_top_customers.html',
                           top_ticket_customers=top_ticket_customers,
                           top_commission_customers=top_commission_customers)



# ###################### Airline Staff Begin##################################
#airline_staff_home
@app.route('/staff_home')  # URL路径
def staff_home():  # 函数名
    # 身份验证 (注意与登录设置保持一致)
    
    if 'username' not in session or session.get('identity') != 'AirlineStaff':
        print(f"Auth failed. Current session: {dict(session)}")
        return redirect(url_for('login'))
    return render_template('staff_home.html') 

# --- 权限控制装饰器 ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'name' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_permission(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if role not in session.get("permissions", []):
                return "Unauthorized", 403
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# Flight Management


#view my flight
@app.route('/view_flights')
@login_required
def view_flights():
    if 'username' not in session or session.get('identity') != 'AirlineStaff':
        return redirect(url_for('login'))
    
    airline = session.get('airline')
    time_range = request.args.get('time_range', 'upcoming')
    
    # Base query
    query = """
    SELECT f.*, COUNT(t.ticket_id) as passenger_count
    FROM flight f
    LEFT JOIN ticket t ON f.flight_num = t.flight_num AND f.airline_name = t.airline_name
    WHERE f.airline_name = %s
    """
    params = [airline]
    
    # Time range filter
    if time_range == 'upcoming':
        query += " AND f.departure_time BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 30 DAY)"
    elif time_range == 'current':
        query += " AND f.departure_time <= NOW() AND f.arrival_time >= NOW()"
    elif time_range == 'past':
        query += " AND f.arrival_time < NOW()"
    # 'all' shows everything
    
    # Additional filters
    if 'departure_airport' in request.args and request.args['departure_airport']:
        query += " AND f.departure_airport = %s"
        params.append(request.args['departure_airport'])
    
    if 'arrival_airport' in request.args and request.args['arrival_airport']:
        query += " AND f.arrival_airport = %s"
        params.append(request.args['arrival_airport'])
    
    if 'date_from' in request.args and request.args['date_from']:
        query += " AND DATE(f.departure_time) >= %s"
        params.append(request.args['date_from'])
    
    if 'date_to' in request.args and request.args['date_to']:
        query += " AND DATE(f.departure_time) <= %s"
        params.append(request.args['date_to'])
    
    # Group and order
    query += " GROUP BY f.flight_num, f.departure_time ORDER BY f.departure_time"
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    flights = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
    cursor.close()
    
    return render_template('staff_view_flight.html', 
                         flights=flights,
                         time_range=time_range)


@app.route('/flight_customers')
@login_required
def flight_customers():
    flight_num = request.args.get('flight_num')
    date = request.args.get('date')
    
    query = """
    SELECT c.name, c.email, t.ticket_id, p.purchase_date
    FROM ticket t
    JOIN customer c ON t.customer_email = c.email
    JOIN purchases p ON t.ticket_id = p.ticket_id
    JOIN flight f ON t.flight_num = f.flight_num AND t.airline_name = f.airline_name
    WHERE t.flight_num = %s AND DATE(f.departure_time) = %s
    AND t.airline_name = %s
    """
    
    cursor = conn.cursor()
    cursor.execute(query, (flight_num, date, session.get('airline')))
    customers = cursor.fetchall()
    print(customers)
    cursor.close()
    
    # Return as HTML snippet for AJAX loading
    html = ""
    for cust in customers:
        html += f"""
        <tr>
            <td>{cust[0]}</td>
            <td>{cust[1]}</td>
            <td>{cust[2]}</td>
            <td>{cust[3].strftime('%Y-%m-%d')}</td>
        </tr>
        """
    
    return html


#create new flight
@app.route('/create_flight', methods=['GET', 'POST'])
@login_required
@require_permission('Admin')
def create_flight():
    airline_name = session['airline']
    # 使用字典型游标以支持 row['column_name']
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 加载 dropdown 数据
    cursor.execute("SELECT airport_name FROM airport")
    airports = [row['airport_name'] for row in cursor.fetchall()]

    cursor.execute("SELECT airplane_id FROM airplane WHERE airline_name = %s", (airline_name,))
    airplanes = [row['airplane_id'] for row in cursor.fetchall()]

    if request.method == 'POST':
        flight_num = request.form['flight_num']
        dep_airport = request.form['departure_airport']
        arr_airport = request.form['arrival_airport']
        dep_time = request.form['departure_time']
        arr_time = request.form['arrival_time']
        price = request.form['price']
        airplane_id = request.form['airplane_id']

        # 校验逻辑
        if dep_airport == arr_airport:
            flash('Departure and arrival airports must be different.', 'danger')
        elif dep_time >= arr_time:
            flash('Departure time must be earlier than arrival time.', 'danger')
        else:
            try:
                cursor.execute("""
                    INSERT INTO flight (
                        airline_name, flight_num, departure_airport, arrival_airport,
                        departure_time, arrival_time, price, status, airplane_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Upcoming', %s)
                """, (airline_name, flight_num, dep_airport, arr_airport,
                      dep_time, arr_time, price, airplane_id))
                conn.commit()
                flash("Flight created successfully!", "success")
                return redirect(url_for('create_flight'))
            except Exception as e:
                conn.rollback()
                print("Error:", e)
                flash("Failed to create flight.", "danger")

    return render_template('staff_create_flights.html',
                           airports=airports,
                           airplanes=airplanes)





#change flight status
def is_operator():
    return 'Operator' in session.get('permissions', [])

@app.route('/change_flight_status')
@login_required
def change_flight_status():
    if not is_operator():
        return render_template('error.html', message="Unauthorized - Operator permission required"), 403

    username = session['username']
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (username,))
        airline = cursor.fetchone()[0]
        session['airline'] = airline  # 用于后续请求

        cursor.execute("SELECT DISTINCT flight_num FROM flight WHERE airline_name = %s", (airline,))
        flight_numbers = cursor.fetchall()

        return render_template('staff_change_status.html', airline=airline, flight_num=flight_numbers)
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        cursor.close()

@app.route('/get_flight_status')
@login_required
def get_flight_status():
    if not is_operator():
        return jsonify({'error': 'Unauthorized'}), 403

    flight_num = request.args.get('flight_num')
    airline = session.get('airline')

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT status FROM flight WHERE flight_num = %s AND airline_name = %s", (flight_num, airline))
        result = cursor.fetchone()

        if result:
            return jsonify({'status': result[0]})
        else:
            return jsonify({'error': 'Flight not found'}), 404
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        cursor.close()

@app.route('/update_flight_status', methods=['POST'])
@login_required
def update_flight_status():
    if not is_operator():
        return jsonify({'error': 'Unauthorized'}), 403

    flight_num = request.form.get('flight_num')
    new_status = request.form.get('new_status')
    airline = session.get('airline')

    if not flight_num or not new_status:
        return jsonify({'error': 'Missing required fields'}), 400

    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE flight SET status = %s WHERE flight_num = %s AND airline_name = %s",
            (new_status, flight_num, airline)
        )
        conn.commit()

        return jsonify({'message': f'Flight {flight_num} status updated to {new_status} successfully'})
    except Exception as e:
        conn.rollback()
        print(f"Error updating status: {e}")
        return jsonify({'error': 'Database error updating status'}), 500
    finally:
        cursor.close()




# System Management

#add airplane
# System Management
@app.route('/add_airplane', methods=['GET', 'POST'])
@login_required
@require_permission('Admin')
def add_airplane():
    if 'username' not in session or session.get('identity') != 'AirlineStaff':
        return redirect(url_for('login'))

    staff_username = session['username']
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (staff_username,))
    result = cursor.fetchone()
    cursor.close()

    if not result:
        return render_template('staff_add_airplane.html', error="Airline not found for staff.")

    airline_name = result['airline_name']

    if request.method == 'POST':
        step = request.form.get('step')

        if step == 'input':
            airplane_id = request.form.get('airplane_id')
            seats = request.form.get('seats')

            if not airplane_id or not seats:
                return render_template('staff_add_airplane.html', error="All fields are required.")

            # 查所有已拥有飞机
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT airplane_id, seats FROM airplane WHERE airline_name = %s", (airline_name,))
            airplanes_owned = cursor.fetchall()
            cursor.close()

            return render_template('staff_confirm_airplane.html',
                           airplane_id=airplane_id,
                           seats=seats,
                           airline_name=airline_name,
                           airplanes_owned=airplanes_owned)

        elif step == 'confirm':
            # 第二阶段，执行插入
            airplane_id = request.form.get('airplane_id')
            seats = request.form.get('seats')

            try:
                cursor = conn.cursor()
                ins = "INSERT INTO airplane (airplane_id, seats, airline_name) VALUES (%s, %s, %s)"
                cursor.execute(ins, (airplane_id, int(seats), airline_name))
                conn.commit()
                cursor.close()
                return render_template('staff_add_airplane.html',
                                       success=f"Airplane {airplane_id} added to {airline_name} successfully!")
            except Exception as e:
                conn.rollback()
                return render_template('staff_add_airplane.html', error="Error: " + str(e))

    return render_template('staff_add_airplane.html')


#add airport

@app.route('/staff/add_airport', methods=['GET', 'POST'])
@login_required
@require_permission('Admin')
def add_airport():
    if 'username' not in session or session.get('identity') != 'AirlineStaff':
        return redirect(url_for('login'))

    error = None
    success = None

    if request.method == 'POST':
        step = request.form.get('step')

        if step == 'input':
            airport_name = request.form.get('airport_name')
            airport_city = request.form.get('airport_city')

            if not airport_name or not airport_city:
                error = "All fields are required."
                return render_template('staff_add_airport.html', error=error)

            # 获取当前航司
            airline_name = session.get('airline_name')

            # 查询该航空公司曾使用过的所有机场
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT DISTINCT a.airport_name, a.airport_city
                FROM airport a
                JOIN (
                    SELECT departure_airport AS airport_name FROM flight WHERE airline_name = %s
                    UNION
                    SELECT arrival_airport AS airport_name FROM flight WHERE airline_name = %s
                ) AS used_airports
                ON a.airport_name = used_airports.airport_name
            """, (airline_name, airline_name))
            airport_list = cursor.fetchall()
            cursor.close()

            return render_template('staff_confirm_airport.html',
                           airport_name=airport_name,
                           airport_city=airport_city,
                           airline_name=airline_name,
                           airport_list=airport_list)


        elif step == 'confirm':
            airport_name = request.form.get('airport_name')
            airport_city = request.form.get('airport_city')

            try:
                cursor = conn.cursor()
                ins = "INSERT INTO airport (airport_name, airport_city) VALUES (%s, %s)"
                cursor.execute(ins, (airport_name, airport_city))
                conn.commit()
                cursor.close()
                success = f"Airport {airport_name} in {airport_city} added successfully!"
            except Exception as e:
                conn.rollback()
                error = "Error: " + str(e)

            return render_template('staff_add_airport.html', success=success, error=error)

    return render_template('staff_add_airport.html')


#add agent 
@app.route('/staff/add_agent', methods=['GET', 'POST'])
@login_required
@require_permission('Admin')
def add_booking_agent():
    if 'username' not in session or session.get('identity') != 'AirlineStaff':
        return redirect(url_for('login'))

    staff_username = session['username']
    airline = session['airline']

    cursor = conn.cursor()

    # 验证是否是 Admin
    cursor.execute("SELECT * FROM permission WHERE username = %s AND (permission_type = 'Admin' or permission_type ='AdminOperator')", (staff_username,))
    is_admin = cursor.fetchone()
    if not is_admin:
        cursor.close()
        flash("Only Admins can add booking agents.")
        return redirect(url_for('staff_home'))

    if request.method == 'POST':
        agent_email = request.form['agent_email']

        # 检查是否存在该 booking agent
        cursor.execute("SELECT * FROM booking_agent WHERE email = %s", (agent_email,))
        agent_exists = cursor.fetchone()
        if not agent_exists:
            flash("This booking agent does not exist.")
        else:
            # 检查是否已添加
            cursor.execute("SELECT * FROM booking_agent_work_for WHERE email = %s AND airline_name = %s", (agent_email, airline))
            already = cursor.fetchone()
            if already:
                flash("This agent already works for your airline.")
            else:
                cursor.execute("INSERT INTO booking_agent_work_for (email, airline_name) VALUES (%s, %s)", (agent_email, airline))
                conn.commit()
                flash("Booking agent added successfully!")

        cursor.close()

    return render_template('staff_add_agent.html')

# Reports & Analytics
@app.route('/view_agents')
@login_required
def view_agents():
    username = session['username']
    
    # 获取代理所在的航空公司
    cursor = conn.cursor()
    query = "SELECT airline_name FROM airline_staff WHERE username = %s"
    cursor.execute(query, (username,))
    airline = cursor.fetchone()
    cursor.close()

    if not airline:
        return "Error: Unable to find the airline for the current user."

    # 获取过去一个月的最活跃代理
    query = """
    SELECT b.email, b.booking_agent_id, COUNT(p.ticket_id) AS ticket_count
    FROM booking_agent b, purchases p, booking_agent_work_for w
    WHERE p.purchase_date >= ADDDATE(DATE(NOW()), INTERVAL -1 MONTH)
    AND w.EMAIL = b.email
    AND w.airline_name = %s
    AND p.booking_agent_id = b.booking_agent_id
    GROUP BY b.email, b.booking_agent_id
    ORDER BY COUNT(p.ticket_id) DESC
    """
    cursor = conn.cursor()
    cursor.execute(query,(airline,))
    top_agents_month = []
    agt = cursor.fetchone()
    count = 1
    
    while agt and count <= 5:
        top_agents_month.append(list(agt))
        agt = cursor.fetchone()
        print('agt1', agt)
        count += 1
    print("top_agents_month:", top_agents_month)
    
    cursor.close()

    # 获取过去一年的最活跃代理
    query = """
    SELECT b.email, b.booking_agent_id, COUNT(p.ticket_id)  AS ticket_count
    FROM booking_agent b, purchases p,booking_agent_work_for w
    WHERE p.purchase_date >= ADDDATE(DATE(NOW()), INTERVAL -12 MONTH)
    AND p.booking_agent_id = b.booking_agent_id
    AND w.EMAIL = b.email
    AND w.airline_name = %s
    GROUP BY b.email, b.booking_agent_id
    ORDER BY COUNT(p.ticket_id) DESC
    """
    cursor = conn.cursor()
    cursor.execute(query,(airline,))
    top_agents_year = []
    agt = cursor.fetchone()
    count = 1
    while agt and count <= 5:
        top_agents_year.append(list(agt))
        agt = cursor.fetchone()
        print('agt2', agt)
        count += 1
    
    print("top_agents_year:", top_agents_year)
    cursor.close()
    

    # 获取过去一年的佣金排名
    query = """
    SELECT b.email, b.booking_agent_id, 0.1*SUM(f.price) 
    FROM booking_agent b, purchases p, ticket t, flight f,booking_agent_work_for w
    WHERE p.purchase_date >= ADDDATE(DATE(NOW()), INTERVAL -12 MONTH)
    AND p.booking_agent_id = b.booking_agent_id
    AND f.flight_num = t.flight_num AND f.airline_name = t.airline_name
    AND t.ticket_id = p.ticket_id
    AND w.EMAIL = b.email
    AND w.airline_name = %s
    GROUP BY b.email, b.booking_agent_id
    ORDER BY SUM(f.price) DESC
    """
    cursor = conn.cursor()
    cursor.execute(query,(airline,))
    top_agents_commission = []
    agt = cursor.fetchone()
    print('agt3' , agt)

    count = 1
    while agt and count <= 5:
        top_agents_commission.append(list(agt))
        agt = cursor.fetchone()
        count += 1
    cursor.close()
    print("top_agents_commission:",top_agents_commission)

    return render_template('staff_view_agent.html', 
                           top_agents_month=top_agents_month,
                           top_agents_year=top_agents_year,
                           top_agents_commission=top_agents_commission,
                           airline=airline[0])


# @app.route('/staff/view_agents')
# @login_required
# def view_agents():
#     if 'username' not in session or session.get('identity') != 'AirlineStaff':
#         return redirect(url_for('login'))

#     airline_name = session['airline']
#     cursor = conn.cursor(pymysql.cursors.DictCursor)

#     # Top 5 by ticket count (past 1 month)
#     cursor.execute("""
#         SELECT booking_agent.email AS agent_email, COUNT(*) AS ticket_count
#         FROM purchases
#         JOIN ticket ON purchases.ticket_id = ticket.ticket_id
#         JOIN booking_agent ON purchases.booking_agent_id = booking_agent.booking_agent_id
#         JOIN flight ON ticket.flight_num = flight.flight_num AND ticket.airline_name = flight.airline_name
#         WHERE flight.airline_name = %s AND purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
#         GROUP BY booking_agent.email
#         ORDER BY ticket_count DESC
#         LIMIT 5
#     """, (airline_name,))
#     top_month = cursor.fetchall()

#     # Top 5 by ticket count (past 1 year)
#     cursor.execute("""
#         SELECT booking_agent.email AS agent_email, COUNT(*) AS ticket_count
#         FROM purchases
#         JOIN ticket ON purchases.ticket_id = ticket.ticket_id
#         JOIN booking_agent ON purchases.booking_agent_id = booking_agent.booking_agent_id
#         JOIN flight ON ticket.flight_num = flight.flight_num AND ticket.airline_name = flight.airline_name
#         WHERE flight.airline_name = %s AND purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
#         GROUP BY booking_agent.email
#         ORDER BY ticket_count DESC
#         LIMIT 5
#     """, (airline_name,))
#     top_year = cursor.fetchall()

#     # Top 5 by commission (past 1 year)
#     cursor.execute("""
#         SELECT booking_agent.email AS agent_email, SUM(price * 0.1) AS total_commission
#         FROM purchases
#         JOIN ticket ON purchases.ticket_id = ticket.ticket_id
#         JOIN booking_agent ON purchases.booking_agent_id = booking_agent.booking_agent_id
#         JOIN flight ON ticket.flight_num = flight.flight_num AND ticket.airline_name = flight.airline_name
#         WHERE flight.airline_name = %s AND purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
#         GROUP BY booking_agent.email
#         ORDER BY total_commission DESC
#         LIMIT 5
#     """, (airline_name,))
#     top_commission = cursor.fetchall()

#     cursor.close()

#     return render_template('staff_view_agents.html',
#                            top_month=top_month,
#                            top_year=top_year,
#                            top_commission=top_commission)





@app.route('/frequent_customers')
@login_required
def frequent_customers():
    if 'username' not in session or session.get('identity') != 'AirlineStaff':
        return redirect(url_for('login'))

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # 获取当前员工所属航空公司
        cursor.execute("SELECT airline_name FROM airline_staff WHERE username = %s", (session['username'],))
        result = cursor.fetchone()
        if not result:
            return "Airline not found for current user", 404
        # airline = result[0]
        airline = result['airline_name']

        selected_email = request.args.get('email')

        # 查询过去一年中乘坐本航空公司航班次数最多的客户
        cursor.execute("""
            SELECT c.email, c.name, c.building_number, c.street, c.city, c.state, 
                   c.phone_number, c.date_of_birth, COUNT(*) as flight_count
            FROM customer c
            JOIN purchases p ON p.customer_email = c.email
            JOIN ticket t ON p.ticket_id = t.ticket_id
            WHERE t.airline_name = %s 
              AND p.purchase_date >= DATE_SUB(NOW(), INTERVAL 1 YEAR)
            GROUP BY p.customer_email
            ORDER BY flight_count DESC
            LIMIT 1
        """, (airline,))
        most_freq_customer = cursor.fetchall()

        # 获取所有客户的邮箱和姓名（供下拉菜单使用）
        cursor.execute("""
            SELECT DISTINCT c.email, c.name
            FROM customer c
            JOIN purchases p ON p.customer_email = c.email
            JOIN ticket t ON t.ticket_id = p.ticket_id
            WHERE t.airline_name = %s
        """, (airline,))
        customers = cursor.fetchall()

        history = []
        if selected_email:
            cursor.execute("""
                SELECT f.flight_num, f.departure_airport, f.arrival_airport,
                       f.departure_time, f.arrival_time, f.status, t.ticket_id, f.price
                FROM flight f
                JOIN ticket t ON f.flight_num = t.flight_num AND f.airline_name = t.airline_name
                JOIN purchases p ON p.ticket_id = t.ticket_id
                WHERE p.customer_email = %s AND f.airline_name = %s
                ORDER BY f.departure_time DESC
            """, (selected_email, airline))
            history = cursor.fetchall()


        return render_template('staff_view_frequent_customers.html',
                               airline=airline,
                               most_freq_customer=most_freq_customer,
                               customers=customers,
                               selected_email=selected_email,
                               history=history)

    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        cursor.close()




@app.route('/staff_view_report', methods=['GET', 'POST'])
@login_required
def staff_view_report():
    # 获取职员所属航空公司
    username = session['username']
    airline_query = "SELECT airline_name FROM airline_staff WHERE username=%s"
    cursor = conn.cursor()
    cursor.execute(airline_query, (username,))
    airline = cursor.fetchone()[0]
    
    # 获取日期范围
    today_date = datetime.now().date()
    last_month_date = today_date - relativedelta(days=30)
    last_year_date = today_date - relativedelta(days=365)
    
    # 初始化自定义范围变量
    custom_range_ticket = None
    
    # 处理自定义日期范围表单
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        custom_query = """
            SELECT COUNT(*) 
            FROM purchases NATURAL JOIN ticket NATURAL JOIN flight 
            WHERE airline_name=%s 
            AND DATE(purchase_date) BETWEEN %s AND %s
        """
        cursor.execute(custom_query, (airline, start_date, end_date))
        custom_range_ticket = cursor.fetchone()[0] or 0
    
    # 查询票数统计
    last_month_ticket_query = """
        SELECT COUNT(*) 
        FROM purchases NATURAL JOIN ticket NATURAL JOIN flight 
        WHERE airline_name=%s 
        AND DATE(purchase_date) BETWEEN %s AND %s
    """
    cursor.execute(last_month_ticket_query, (airline, last_month_date, today_date))
    last_month_ticket = cursor.fetchone()[0] or 0
    
    last_year_ticket_query = """
        SELECT COUNT(*) 
        FROM purchases NATURAL JOIN ticket NATURAL JOIN flight 
        WHERE airline_name=%s 
        AND DATE(purchase_date) BETWEEN %s AND %s
    """
    cursor.execute(last_year_ticket_query, (airline, last_year_date, today_date))
    last_year_ticket = cursor.fetchone()[0] or 0
    
    # 月度数据查询
    monthly_query = """
        SELECT DATE_FORMAT(purchase_date, '%%Y-%%m') as month, 
               COUNT(*) as count
        FROM purchases NATURAL JOIN ticket NATURAL JOIN flight
        WHERE airline_name=%s
        AND purchase_date >= DATE_SUB(NOW(), INTERVAL 1 YEAR)
        GROUP BY DATE_FORMAT(purchase_date, '%%Y-%%m')
        ORDER BY month
    """
    cursor.execute(monthly_query, (airline,))
    monthly_data_raw = cursor.fetchall()
    cursor.close()
    
    # 处理图表数据
    monthly_data = {}
    monthly_labels = []
    monthly_values = []
    
    # 生成过去12个月的标签
    current_date = datetime.now()
    for i in range(12):
        month_date = current_date - relativedelta(months=i)
        month_str = month_date.strftime('%Y-%m')
        monthly_data[month_str] = 0
        monthly_labels.append(month_str)
    
    # 填充实际数据
    for row in monthly_data_raw:
        monthly_data[row[0]] = row[1]
    
    # 反转顺序(从旧到新)
    monthly_labels.reverse()
    monthly_values = [monthly_data[month] for month in monthly_labels]
    
    return render_template(
        "staff_view_report.html",
        airline=airline,
        today_date=today_date.strftime('%Y-%m-%d'),
        last_month_date=last_month_date.strftime('%Y-%m-%d'),
        last_year_date=last_year_date.strftime('%Y-%m-%d'),
        last_month_ticket=last_month_ticket,
        last_year_ticket=last_year_ticket,
        custom_range_ticket=custom_range_ticket,
        monthly_data=monthly_data,
        monthly_labels=monthly_labels,
        monthly_values=monthly_values
    )

@app.route('/revenue_comparison')
@login_required
def staff_revenue_comparison():
    username = session['username']
    
    # Get airline name
    airline_query = "SELECT airline_name FROM airline_staff WHERE username=%s"
    cursor = conn.cursor()
    cursor.execute(airline_query, (username,))
    airline = cursor.fetchone()[0]
    
    # Get date ranges
    today_date_query = "SELECT DATE(NOW())"
    cursor.execute(today_date_query)
    today_date = cursor.fetchone()[0]
    
    last_month_date_query = "SELECT DATE_SUB(DATE(NOW()), INTERVAL 30 DAY)"
    cursor.execute(last_month_date_query)
    last_month_date = cursor.fetchone()[0]
    
    last_year_date_query = "SELECT DATE_SUB(DATE(NOW()), INTERVAL 365 DAY)"
    cursor.execute(last_year_date_query)
    last_year_date = cursor.fetchone()[0]
    
    # Last month revenue
    non_agent_last_month_query = """
        SELECT COALESCE(SUM(price), 0) 
        FROM flight NATURAL JOIN purchases NATURAL JOIN ticket 
        WHERE airline_name=%s AND booking_agent_id IS NULL 
        AND purchase_date BETWEEN %s AND %s
    """
    cursor.execute(non_agent_last_month_query, (airline, last_month_date, today_date))
    non_agent_last_month = int(cursor.fetchone()[0])
    
    agent_last_month_query = """
        SELECT COALESCE(SUM(price), 0) 
        FROM flight NATURAL JOIN purchases NATURAL JOIN ticket 
        WHERE airline_name=%s AND booking_agent_id IS NOT NULL 
        AND purchase_date BETWEEN %s AND %s
    """
    cursor.execute(agent_last_month_query, (airline, last_month_date, today_date))
    agent_last_month = int(cursor.fetchone()[0])
    
    # Last year revenue
    non_agent_last_year_query = """
        SELECT COALESCE(SUM(price), 0) 
        FROM flight NATURAL JOIN purchases NATURAL JOIN ticket 
        WHERE airline_name=%s AND booking_agent_id IS NULL 
        AND purchase_date BETWEEN %s AND %s
    """
    cursor.execute(non_agent_last_year_query, (airline, last_year_date, today_date))
    non_agent_last_year = int(cursor.fetchone()[0])
    
    agent_last_year_query = """
        SELECT COALESCE(SUM(price), 0) 
        FROM flight NATURAL JOIN purchases NATURAL JOIN ticket 
        WHERE airline_name=%s AND booking_agent_id IS NOT NULL 
        AND purchase_date BETWEEN %s AND %s
    """
    cursor.execute(agent_last_year_query, (airline, last_year_date, today_date))
    agent_last_year = int(cursor.fetchone()[0])
    
    cursor.close()
    
    return render_template(
        'staff_revenue_comparison.html',
        airline=airline,
        today_date=today_date,
        last_month_date=last_month_date,
        last_year_date=last_year_date,
        non_agent_last_month=non_agent_last_month,
        agent_last_month=agent_last_month,
        non_agent_last_year=non_agent_last_year,
        agent_last_year=agent_last_year
    )

# Additional Features
@app.route('/top_destinations')
@login_required
def staff_top_destination():
    username = session['username']
    
    cursor = conn.cursor()
    # Select the airline that staff works for
    query = "SELECT airline_name FROM airline_staff WHERE username = %s"
    cursor.execute(query, (username,))
    airline = cursor.fetchone()
    
    if not airline:
        cursor.close()
        return "Error: Staff not associated with any airline", 400
    
    # Query for top destinations in the past 3 months
    month_query = """
        SELECT f.arrival_airport, a.airport_city, COUNT(p.customer_email) as ticket_count
        FROM purchases p
        JOIN ticket t ON p.ticket_id = t.ticket_id
        JOIN flight f ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
        JOIN airport a ON a.airport_name = f.arrival_airport
        WHERE f.airline_name = %s 
        AND f.arrival_time BETWEEN DATE_SUB(NOW(), INTERVAL 3 MONTH) AND NOW()
        GROUP BY f.arrival_airport, a.airport_city 
        ORDER BY ticket_count DESC
        LIMIT 3
    """
    cursor.execute(month_query, (airline[0],))
    destination_month = cursor.fetchall()
    
    # Query for top destinations in the past year
    year_query = """
        SELECT f.arrival_airport, a.airport_city, COUNT(p.customer_email) as ticket_count
        FROM purchases p
        JOIN ticket t ON p.ticket_id = t.ticket_id
        JOIN flight f ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
        JOIN airport a ON a.airport_name = f.arrival_airport
        WHERE f.airline_name = %s 
        AND f.arrival_time BETWEEN DATE_SUB(NOW(), INTERVAL 1 YEAR) AND NOW()
        GROUP BY f.arrival_airport, a.airport_city 
        ORDER BY ticket_count DESC
        LIMIT 3
    """
    cursor.execute(year_query, (airline[0],))
    destination_year = cursor.fetchall()
    
    cursor.close()
    
    return render_template('staff_top_destination.html', 
                         destination_month=destination_month,
                         destination_year=destination_year)


#grand permission
@app.route('/staff/grant_permission', methods=['GET', 'POST'])
@login_required
@require_permission('Admin')
def grant_permission():
    if 'username' not in session or session.get('identity') != 'AirlineStaff':
        return redirect(url_for('login'))

    current_user = session['username']
    airline_name = session['airline']

    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT * FROM permission 
        WHERE username = %s AND (permission_type = 'Admin' or Permission_type = 'AdminOperator')
    """, (current_user))




    is_admin = cursor.fetchone()
    if not is_admin:
        cursor.close()
        flash("Only Admins can grant permissions.")
        return redirect(url_for('staff_home'))

    if request.method == 'POST':
        target_user = request.form['target_user']
        new_permission = request.form['new_permission']

        # Check if the target staff belongs to the same airline
        cursor.execute("""
            SELECT * FROM airline_staff 
            WHERE username = %s AND airline_name = %s
        """, (target_user, airline_name))
        staff_check = cursor.fetchone()

        if not staff_check:
            flash("Staff not found or not in your airline.")
        else:
            granted = []
            duplicate = []

            permissions_to_add = []
            if new_permission == 'Admin and Operator':
                permissions_to_add = ['Admin', 'Operator']
            else:
                permissions_to_add = [new_permission]

            for perm in permissions_to_add:
                cursor.execute("""
                        SELECT * FROM permission 
                        WHERE username = %s AND permission_type = %s
                    """, (target_user, perm))
                exists = cursor.fetchone()
                if exists:
                    duplicate.append(perm)
                else:
                    cursor.execute("""
                        INSERT INTO permission (username, permission_type) 
                        VALUES (%s, %s)
                    """, (target_user,perm))
                    granted.append(perm)

            conn.commit()

            if granted:
                flash(f"Granted permission(s): {', '.join(granted)} to {target_user}.")
            if duplicate:
                flash(f"{target_user} already has permission(s): {', '.join(duplicate)}.")

    cursor.execute("""
        SELECT username FROM airline_staff 
        WHERE airline_name = %s AND username != %s
    """, (airline_name, current_user))
    staff_list = [row['username'] for row in cursor.fetchall()]
    cursor.close()

    return render_template('staff_grant_permission.html', staff_list=staff_list)


# ========== 主程序入口 ==========
if __name__ == '__main__':
    app.run(debug=True)
