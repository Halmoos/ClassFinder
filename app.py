from flask import Flask, request, redirect
import mysql.connector
from flask import render_template, flash, session, g
from flask_bootstrap import Bootstrap
from datetime import timedelta, datetime, time

app = Flask(__name__)
Bootstrap(app)
app.secret_key = "key"
database = mysql.connector.connect(host="localhost",
                                   user="root",
                                   password="pass123123",
                                   database="classroom")

cursor = database.cursor(buffered=True)



@app.before_request
def before_request():
    g.user = None
    cursor.execute("select * from student")
    all_students = cursor.fetchall()
    cursor.execute("select * from instructor")
    all_instructors = cursor.fetchall()
    all_users = all_instructors + all_students
    if 'user_id' in session:
        user = [x for x in all_users if x[0] == session['user_id']][0]
        g.user = user

@app.route('/', methods=["POST", "GET"])
def classroom():

    g.showrooms = False
    if session.get('logged_in') != True or g.user == None:
        return redirect('/login')
    cursor.execute("select DISTINCT start_time from time_slot")
    start_times = cursor.fetchall()
    converted_start = []
    for time in start_times:
        converted = (datetime(1, 1, 1, 0, 0, 0) + time[0]).time()
        converted_start.append(converted)
    sorted((converted_start), reverse=True)

    cursor.execute("select DISTINCT end_time from time_slot")
    end_times = cursor.fetchall()
    converted_end = []
    for time in end_times:
        converted = (datetime(1, 1, 1, 0, 0, 0) + time[0]).time()
        converted_end.append(converted)
    sorted((converted_end), reverse=True)

    cursor.execute("select DISTINCT day_time from time_slot")
    days = cursor.fetchall()
    g.start_times = converted_start
    g.end_times = converted_end
    g.days = days

    if request.method == 'POST':
        g.invalid = False
        start = request.form["start"]
        end = request.form["end"]
        day = request.form["day"]
        print(start, end, day)
        if start == 'Start time' or end == 'End Time' or day == 'Day':
            g.invalid = True
        else:
            cursor.execute("select * from time_slot where start_time >= %s and end_time <= %s and day_time = %s",(start,end,day))
            timeslots = cursor.fetchall()
            # print(timeslots)


            time_sec = []
            for i in timeslots:
                cursor.execute("select section_id,time_slot_id from sec_time where time_slot_id = %s",(i[0],))
                temp = cursor.fetchall()
                time_sec.append(temp)
            # print(time_sec)


            sections = []
            for list in time_sec:
                for i in list:
                    sections.append(i[0])
            sections = set(sections)
            # print(sections)

            related_sections = []
            for i in sections:
                cursor.execute("select * from section where section_id = %s", (i,))
                temp = cursor.fetchall()
                related_sections.append(temp)
            # print(related_sections)
            room_ids = []
            for i in related_sections:
                room_ids.append(i[0][4])
            room_ids = [i for i in room_ids if i]  # removing None
            #print(room_ids)
            cursor.execute("select * from classrooms where room_name NOT IN {}".format(tuple(room_ids)))
            result = cursor.fetchall()
            #print(result)

            time_results = []
            for room in result:  # Finding the upcoming lecture time for each room
                room_min = None
                all_lec_starts = []
                cursor.execute("select section_id,sec_classroom from section where sec_classroom =%s", (room[0],))
                lecs = cursor.fetchall()
                #print(lecs)
                for j in lecs:
                    cursor.execute("select section_id, time_slot_id from sec_time where section_id =%s", (j[0],))
                    try:
                        earliest_slot = cursor.fetchall()[0]
                    except IndexError:
                        print('Unhandeled error')
                    #print(earliest_slot)
                    cursor.execute("select start_time from time_slot where start_time > %s and time_slot_id = %s", (start,earliest_slot[1]))
                    try:
                        lec_start_time = cursor.fetchall()[0]
                    except IndexError:
                        lec_start_time = [None]
                    #print(lec_start_time[0])
                    if lec_start_time[0] is not None:
                        x = (datetime(1, 1, 1, 0, 0, 0) + lec_start_time[0]).time()  # to time obj conversion
                        all_lec_starts.append(x)
                    if len(all_lec_starts) == 0:
                        room_min = 'Free'
                    else:
                        #print(all_lec_starts)
                        room_min = min(all_lec_starts)
                #print("Free until:", room_min)
                time_results.append(room_min)

            final = [[x[0], x[1], x[2]] for x in result]
            for i in range(len(final)):
                final[i].append(time_results[i])

            print(final)
            g.time_results = time_results
            g.showrooms = True
            g.result = final

    return render_template('main.html')


@app.route("/login", methods=["POST","GET"])
def login():

    if request.method == "GET":
        return render_template("login.html")
    else:

        cursor.execute("select * from student")
        all_students = cursor.fetchall()
        cursor.execute("select * from instructor")
        all_instructors = cursor.fetchall()
        all_users = all_instructors + all_students

        session.pop('user_id', None)
        session.pop('logged_in', None)
        session.pop('username', None)
        username = request.form["username"]
        userpass = request.form["pass"]

        login = False
        user = [x for x in all_users if x[1].lower() == username.lower()][0]
        if user and user[2] == userpass:
           login = True
           g.user = user
           session['user_id'] = user[0]
           session['username'] = user[1]
           session['logged_in'] = True

        if login == True:
            return redirect("/")
        else:
            flash('Username or password is incorrect.')
            return redirect("/login")


@app.route("/logout")
def logout():

    session.pop('user_id', None)
    session.pop('logged_in', None)
    session.pop('username', None)
    g.user = None
    return redirect("/login ")



@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":

        return render_template("register.html")

    else:

        username = request.form["username"]
        usertype = request.form["usertype"]
        password = request.form["password"]
        confirm = request.form["password_confirm"]

        print(username, usertype, password, confirm)

        if password != confirm:
            flash("Passwords do not match!", "info")
            print("Match failed")
            return redirect("/register")
        
        if usertype == "Instructor":
            cursor.execute("select * from instructor")
            all_users = cursor.fetchall()
            print(all_users)
            check = True
            for user in all_users:
                if username.lower() == user[1].lower():
                    check = False
                    flash("User already created")
            if check == True:
                cursor.execute("insert into instructor(name,password)"
                               "values(%s,%s)", (username, password))

                database.commit()
                return redirect("/")
            else:
                return redirect("/register")

        if usertype == "Student":
            cursor.execute("select * from student")
            all_users = cursor.fetchall()
            print(all_users)
            check = True
            for user in all_users:
                if username.lower() == user[1].lower():
                    check = False
                    flash("User already created")
            if check == True:
                cursor.execute("insert into student(name,password)"
                               "values(%s,%s)", (username, password))

                database.commit()
                return redirect("/")
            else:
                return redirect("/register")

        return redirect("/")

@app.route("/instructor", methods=["POST","GET"])
def instructor():

    if session.get('logged_in') != True or g.user == None:
        return redirect('/login')
    g.showinst = False
    g.none = False
    cursor.execute("select name from instructor")
    instructors = cursor.fetchall()
    instructors_list = [x[0] for x in instructors]

    if request.method == 'POST':
        search = request.form['search']
        cursor.execute("select * from instructor where name = %s",(search,))
        inst = cursor.fetchone()
        print(inst)
        g.showinst = True
        g.inst = inst
        if inst is None:
            g.none = True
            g.showinst = False

        # Finding lectures for this professor
        cursor.execute("select title, Instructor from section where Instructor = %s", (search,))
        sections = cursor.fetchall()
        print(sections)
        g.sections = sections

    return render_template("instructor.html", instructors = instructors_list)

@app.route("/lectures", methods=["POST","GET"])
def lectures():

    if session.get('logged_in') != True or g.user == None:
        return redirect('/login')
    g.showlect = False
    g.none2 = False
    g.noroom = False
    cursor.execute("select title from section")
    sects = cursor.fetchall()
    sects_list = [x[0] for x in sects]
    if request.method == 'POST':
        search = request.form['search']
        cursor.execute("select * from section where title = %s",(search,))
        lecture = cursor.fetchone()
        print(lecture)
        if lecture is None:
            g.none2 = True
        else:
            if lecture[4] is None:
                g.noroom = True
                info = [lecture[5],'No classroom', lecture[6]]
                g.info = info
                g.times = []
            else:
                cursor.execute("select * from classrooms where room_name = %s",(lecture[4],))
                room = cursor.fetchone()
                print(room)
                info = [lecture[5],room[2]+'#'+room[0],lecture[6]]
                g.info = info

                cursor.execute("select section_id,time_slot_id from sec_time where section_id = %s",(lecture[0],))
                slots = cursor.fetchall()
                #print(slots)
                times = []
                for slot in slots:
                    cursor.execute("select * from time_slot where time_slot_id = %s",(slot[1],))
                    x = cursor.fetchone()
                    times.append(x)
                #print(times)
                days = set(map(lambda x: x[1], times))
                newlist = [[(y[1],y[2],y[3]) for y in times if y[1] == x] for x in days]  # new list per day data
                #print(newlist)
                result = []
                for list in newlist:
                    day = list[0][0]
                    starts = [x[1] for x in list]
                    ends = [x[2] for x in list]
                    start = min(starts)
                    end = max(ends)
                    print(day,start,end)
                    result.append((day,start,end))
                g.times = result

            g.showlect = True

    return render_template("lectures.html", sects=sects_list)