import flask
import click
from flask import request, jsonify, g, Flask, abort
import sqlite3
from flask_basicauth import BasicAuth

app = flask.Flask( __name__ )
app.config[ "DEBUG" ] = True

#connect to database
DATABASE = 'database.db'

def get_db():
    db = getattr( g, '_database', None )
    if db is None:
        db = g._database = sqlite3.connect( DATABASE )
    return db 

#close database connection
@app.teardown_appcontext
def close_connection( exception ):
    db = getattr( g, '_database', None )
    if db is not None:
        db.close()

#initialize database with data from a separate file
@app.cli.command( "init_db" )
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource( 'init.sql', mode='r' ) as f:
            db.cursor().executescript( f.read() )
        db.commit()
    print( "Initialized database" )

#return items as a dictionary, not a list
def dict_factory( cursor, row ):
    d = {}
    for idx, col in enumerate( cursor.description ):
        d[ col[ 0 ] ] = row[ idx ]
    return d

#check credentials from database
class auth_override( BasicAuth ):
    user = ""
    def __init__( self, app=None ):
        self.app = app 

    def check_credentials( self, username, password ):
        query = "SELECT * FROM User WHERE username='" + username + "' AND pssword='" + password + "'"

        conn = sqlite3.connect( 'database.db' )
        conn.row_factory = dict_factory
        cur = conn.cursor()

        results = cur.execute( query ).fetchall()

        if not results:
            return False
        else:
            auth_override.user = username
            self.app.config[ 'BASIC_AUTH_USERNAME' ] = username
            self.app.config[ 'BASIC_AUTH_PASSWORD' ] = password
            return True
    
    def get_user( self ):
        return auth_override.user

#Home page
@app.route( '/', methods=[ 'GET' ] )
def home():
    return "<h1>Web Service API</h1><h2>By: Katelyn Jaing</h2><p>List all forums: /forums </p><p>List all threads in a specified forum: /forums/[forumId] </p><p>List all posts in a specified thread: /forums/[forumId]/[threadId] </p><p>Create a forum: /forums?fname=forumName</p><p>Create a thread: /forums/[forumId]?title=threadTitle&ptext=firstPost</p><p>Create a post: /forums/[forumId]/[threadId]?ptext=postText</p><p>Create a user: /users?username=user&pssword=password</p><p>Change password: /users/[username]?pssword=newPassword</p>"

#List all available discussion forums
@app.route( '/forums', methods=[ 'GET' ] )
def list_forums():
    query = "SELECT * FROM Forum;"
    
    conn = sqlite3.connect( 'database.db' )
    conn.row_factory = dict_factory
    cur = conn.cursor()

    results = cur.execute( query ).fetchall()

    return jsonify( results )

#Create a new discussion forum
basic_auth = auth_override( app )
@app.route('/forums', methods=[ 'POST' ] )
@basic_auth.required
def make_forum():
    creator = basic_auth.get_user()

    if request.method == 'POST':
        forum_name = request.args.get( 'fname' )

        #check if forum already exists
        query = "SELECT * FROM Forum WHERE fname='" + forum_name +"'"

        conn = sqlite3.connect( 'database.db' )
        conn.row_factory = dict_factory
        cur = conn.cursor()
        results = cur.execute( query ).fetchone()
        if results:
            abort( 409)
        else: #forum doesn't exist, enter it into the database
            query = "INSERT INTO Forum( fname, creator ) VALUES( '" + forum_name + "', '" + creator + "')"

            conn = sqlite3.connect( 'database.db' )
            cur = conn.cursor()
            cur.execute( query )
            conn.commit()
            
            return "<h1>HTTP 200</h1><p>Forum created successfully by " + creator + "</p>"


#List threads in the specified forum
@app.route( '/forums/<forum_id>', methods=[ 'GET' ] )
def list_threads( forum_id ):
    forum = forum_id

    query = "SELECT * FROM Thread WHERE forumId=" + forum
   
    conn = sqlite3.connect( 'database.db' )
    conn.row_factory = dict_factory
    cur = conn.cursor()
   
    results = cur.execute( query ).fetchall()

    if not results:
        abort( 404 )
    else:
        return jsonify( results )

#Create a new thread in the specified forum
basic_auth = auth_override( app )
@app.route( '/forums/<forum_id>', methods=[ 'POST' ] )
@basic_auth.required
def make_thread( forum_id ):
    creator = basic_auth.user
    
    if request.method == 'POST':
        #check if forum exists
        query = "SELECT * FROM Forum WHERE forumId=" + forum_id

        conn = sqlite3.connect( 'database.db' )
        cur = conn.cursor()
        results = cur.execute( query ).fetchone()
        
        if results: #forum exists
            thread_title = request.args.get( "title" )
            post_text = request.args.get( "ptext" )

            #create new thread
            query = "INSERT INTO Thread( title, creator, forumId ) VALUES( '" + thread_title + "', '" + creator + "', " + forum_id + ")"

            conn = sqlite3.connect( 'database.db' )
            cur = conn.cursor()
            cur.execute( query )
            conn.commit()

            #get the new thread's threadId
            query = "SELECT threadId FROM Thread WHERE title='" + thread_title + "' AND creator='" + creator + "' AND forumId=" + forum_id

            conn = sqlite3.connect( 'database.db' )
            cur = conn.cursor()

            results = cur.execute( query ).fetchone()
            thread_id = str( results[ 0 ] )

            #create first post
            query = "INSERT INTO Post( author, ptext, threadId ) VALUES( '" + creator + "', '" + post_text + "', " + thread_id + ")"

            conn = sqlite3.connect( 'database.db' )
            cur = conn.cursor()
            cur.execute( query )
            conn.commit()

            return "<h1>HTTP 200</h1><p>New thread and post added to forum " + forum_id + "</p>"
        else:
            abort( 404 )

#List posts to the specified thread
@app.route( '/forums/<forum_id>/<thread_id>', methods=[ 'GET' ] )
def list_posts( forum_id, thread_id ):
    forum = forum_id
    thread = thread_id

    query = "SELECT Post.author, Post.ptext, Post.time_stamp FROM Post INNER JOIN Thread ON Thread.threadId = Post.threadId WHERE Thread.forumId=" + forum + " AND Thread.threadId=" + thread

    conn = sqlite3.connect( 'database.db' )
    conn.row_factory = dict_factory
    cur = conn.cursor()
   
    results = cur.execute( query ).fetchall()

    if not results:
        abort( 404 )
    else:
        return jsonify( results )

#Add a new post to the specified thread
basic_auth = auth_override( app )
@app.route( '/forums/<forum_id>/<thread_id>', methods=[ 'POST' ] )
@basic_auth.required
def make_post( forum_id, thread_id ):
    creator = basic_auth.user

    #check if forum exists
    query = "SELECT * FROM Forum WHERE forumId=" + forum_id

    conn = sqlite3.connect( 'database.db' )
    cur = conn.cursor()
    results = cur.execute( query ).fetchone()
    
    if results: #forum exists
        #check if thread exists
        query = "SELECT * FROM Thread WHERE threadId=" + thread_id
        
        conn = sqlite3.connect( 'database.db' )
        cur = conn.cursor()
        results2 = cur.execute( query ).fetchone()
        if results2: #thread exists
            post_text = request.args.get( "ptext" )

            query = "INSERT INTO Post( author, ptext, threadId ) VALUES( '" + creator + "', '" + post_text + "', " + thread_id + ")"

            conn = sqlite3.connect( 'database.db' )
            cur = conn.cursor()
            results3 = cur.execute( query )
            conn.commit()

            return "<h1>HTTP 200</h1><p>Post created successfully</p>"

        else:
            abort( 404 )
    else:
        abort( 404 )

#Create a new user
@app.route( '/users', methods=[ 'POST' ] )
def make_user():
    #get user input
    new_username = request.args.get( 'username' )
    new_password = request.args.get( 'pssword' )

    #check if username exists
    query = "SELECT * FROM User WHERE username='" + new_username + "'"

    conn = sqlite3.connect( 'database.db' )
    cur = conn.cursor()
    results = cur.execute( query ).fetchone()
    
    if results: #user already exists
        abort( 409 )
    else:
        query = "INSERT INTO User VALUES( '" + new_username + "', '" + new_password + "')"

        conn = sqlite3.connect( 'database.db' )
        cur = conn.cursor()
        cur.execute( query )
        conn.commit()

        return "<h1>HTTP 200</h1><p>New user created!</p>"

#Changes a user's password
basic_auth = auth_override( app )
@app.route( '/users/<username>', methods=[ 'PUT' ] )
@basic_auth.required
def change_password( username ):
    #check if username exist
    query = "SELECT * FROM User WHERE username='" + username + "'"

    conn = sqlite3.connect( 'database.db' )
    cur = conn.cursor()
    results = cur.execute( query ).fetchone()

    if results: #username exists
        #check if username is the same as current authenticated user
        if username == basic_auth.user: #username and authenticated user same
            new_password = request.args.get( 'pssword' )

            query = "UPDATE User SET pssword='" + new_password + "' WHERE username='" + username + "'"

            conn = sqlite3.connect( 'database.db' )
            cur = conn.cursor()
            cur.execute( query )
            conn.commit()

            return "<h1>HTTP 200</h1><p>Password updated</p>"
        else:
            abort(409)
    else:
        abort( 404 )

'''
#List users 
@app.route( '/users', methods=[ 'GET' ] )
def list_users():
    query = "SELECT * FROM User"
    conn = sqlite3.connect( 'database.db' )
    conn.row_factory = dict_factory
    cur = conn.cursor()
   
    results = cur.execute( query ).fetchall()
    return jsonify( results )
'''