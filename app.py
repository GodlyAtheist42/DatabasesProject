from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.debug import DebuggedApplication
from pymysql import cursors
import pymysql
import hashlib

SALT = 'cs3083'

app = Flask(__name__)

conn = pymysql.connect(host = '127.0.0.1',
                       user = 'root',
                       port = 8889,
                       password = 'root',
                       db = 'finsta',
                       charset = 'utf8mb4',
                       )
app.secret_key = "key"
@app.route('/')
def hello():
    return render_template('index.html')

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/register")
def register():
    return render_template('register.html')

@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    
    cursor.execute(query, (username, hashed_password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password'] + SALT
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person(username, password, firstName, lastName) VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (username, hashed_password, firstName, lastName))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT filepath, caption, photoPoster, photoID \
             FROM photo \
             WHERE (allFollowers = 1 AND photoPoster in (SELECT username_followed FROM follow WHERE username_follower = %s AND followStatus = 1)) \
             OR \
             (      photoID in (SELECT PhotoId \
				    FROM SharedWith \
					WHERE (groupName,groupOwner ) IN (SELECT groupName,owner_username \
                                                          FROM BelongTo \
					                                      WHERE member_username = %s)\
			))'

    cursor.execute(query,(user, user))
    data = cursor.fetchall()
    query = 'SELECT username_follower FROM follow WHERE username_followed = %s AND followStatus=0'
    cursor.execute(query,user)
    data2 = cursor.fetchall()
    query = 'SELECT groupName FROM belongTo WHERE member_username = %s'
    cursor.execute(query,user)
    data3 = cursor.fetchall()
    query = 'SELECT photoID from tagged WHERE username = %s AND tagStatus = 0'
    cursor.execute(query, user)
    data4 = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, photoData=data, followers = data2, groups = data3, tagRequests = data4)

@app.route('/followRequest', methods=['GET','POST'])
def followRequest():
    followed = session['username']
    follower = request.args.get("follower")
    followStatus = int(request.args.get("fs"))
    cursor = conn.cursor()
    query = 'DELETE FROM follow WHERE username_followed = %s AND username_follower = %s'
    cursor.execute(query, (followed, follower))
    if followStatus:
        query = 'INSERT INTO follow VALUES(%s, %s, 1)'
        cursor.execute(query, (followed, follower))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))
        
@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor()
    link = request.form['photoPath']
    caption = request.form['caption']
    groups = request.form['groupList']
    allFollowTrue = int(request.form['allFollow'])
    query = 'SELECT max(photoID) FROM photo'
    cursor.execute(query,)
    pid = cursor.fetchone()

    if not pid:
        pid = (0)
    pid = pid[0] + 1

    query = 'INSERT INTO photo (photoID, caption, filePath, photoPoster, allFollowers) VALUES(%s, %s, %s, %s, %s)'
    cursor.execute(query, (pid, caption, link, username, allFollowTrue))
    conn.commit()

    if not allFollowTrue:
        groupList = groups.split(',')
        for group in groupList:
            query = 'SELECT owner_username FROM belongTo where member_username = %s AND groupName = %s'
            cursor.execute(query, (username, group))
            owner = cursor.fetchone()
            query = 'INSERT INTO sharedwith VALUES(%s, %s, %s)'
            cursor.execute(query, (owner, group, pid))
            conn.commit()
    cursor.close()


    cursor.close()
    return redirect(url_for('home'))

@app.route('/photoDetails', methods=['GET', 'POST'])
def photoDetails():
    pid = request.args.get("id")
    cursor = conn.cursor()
    query = 'SELECT * FROM photo JOIN person on (photo.photoPoster = person.username) WHERE photoID = %s'
    cursor.execute(query, (pid))
    data = cursor.fetchone()
    query = 'SELECT firstName, lastName FROM tagged NATURAL JOIN person WHERE photoID = %s'
    cursor.execute(query, (pid))
    data2 = cursor.fetchall()
    cursor.close()
    return render_template('photoDetails.html', details = data, taggedList = data2)

@app.route('/createGroup', methods=['GET', 'POST'])
def createGroup():
    groupName = request.form['groupName']
    owner = session['username']
    description = request.form['description']
    cursor = conn.cursor()
    query = 'INSERT INTO friendgroup (groupOwner, groupName, description) VALUES(%s, %s, %s)'
    cursor.execute(query, (owner, groupName, description))
    conn.commit()
    query = 'INSERT INTO belongTo VALUES (%s, %s, %s)'
    cursor.execute(query, (owner, owner, groupName))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/follow', methods=['GET', 'POST'])
def follow():
    followed = request.form['followed']
    follower = session['username']
    cursor = conn.cursor()
    query = 'INSERT INTO follow (username_followed, username_follower, followstatus) VALUES (%s, %s, 0)'
    cursor.execute(query, (followed, follower))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/tag', methods=['GET', 'POST'])
def tag():
    user = session['username']
    cursor = conn.cursor()
    toTag = request.form['toTag']
    pid = request.args.get('id')
    if toTag == user:
        query = 'INSERT INTO tagged VALUES(%s, %s, 1)'
        cursor.execute(query, (toTag, pid))
        conn.commit()
    else:
        query = 'SELECT photoID \
             FROM photo \
             WHERE photoID = %s AND ((allFollowers = 1 AND photoPoster in (SELECT username_followed FROM follow WHERE username_follower = %s AND followStatus = 1)) \
             OR \
             (      photoID in (SELECT PhotoId \
				    FROM SharedWith \
					WHERE (groupName,groupOwner ) IN (SELECT groupName,owner_username \
                                                          FROM BelongTo \
					                                      WHERE member_username = %s)\
			)))'
        cursor.execute(query, (pid, toTag, toTag))
        data = cursor.fetchone()
        if data:
            query = 'INSERT INTO tagged VALUES(%s, %s, 0)'
            cursor.execute(query, (toTag, pid))
            conn.commit()
        else:
            flash("The tagged person can't see the photo.")
            return redirect(url_for('home'))
        cursor.close()

    return redirect(url_for('home'))

@app.route('/tagRequest', methods=['GET', 'POST'])
def tagRequest():
    user = session['username']
    cursor = conn.cursor()
    ts = request.args.get('ts')
    pid = request.args.get('pid')
    query = 'DELETE FROM tagged WHERE username = %s AND photoID = %s'
    cursor.execute(query, (user, pid))
    conn.commit()
    if int(ts):
        query = 'INSERT INTO tagged VALUES(%s, %s, 1)'
        cursor.execute(query, (user, pid))
        conn.commit()
        cursor.close()
    return redirect(url_for('home'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    user = session['username']
    cursor = conn.cursor()
    pid = request.form['searchUser']
    if user != pid:
        query = 'SELECT filepath, caption, photoPoster, photoID \
                 FROM photo \
                 WHERE (photoPoster = %s) AND ((allFollowers = 1 AND photoPoster in (SELECT username_followed FROM follow WHERE username_follower = %s AND followStatus = 1)) \
                 OR \
                 (      photoID in (SELECT PhotoId \
                        FROM SharedWith \
                        WHERE (groupName,groupOwner ) IN (SELECT groupName,owner_username \
                                                              FROM BelongTo \
                                                              WHERE member_username = %s)\
                )))'
        cursor.execute(query, (pid, user, user))
    else:
        query = 'SELECT filepath, caption, photoPoster, photoID \
                 FROM photo\
                 WHERE photoPoster = %s'
        cursor.execute(query, (user))

    data = cursor.fetchall()
    cursor.close()
    return render_template('searchresults.html', photoData=data)


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

if __name__ == "__main__":
    app.run