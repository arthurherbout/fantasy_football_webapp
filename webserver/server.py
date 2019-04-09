#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver
To run locally
    python server.py
Go to http://localhost:8111 in your browser
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of:
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "ah3617"
DB_PASSWORD = "coPQEi186E"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
#engine.execute("""DROP TABLE IF EXISTS test;""")
#engine.execute("""CREATE TABLE IF NOT EXISTS test (
#  id serial,
#  name text
#);""")
#engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request
  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:
  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2
  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT username FROM users")
  names = []
  for result in cursor:
    names.append(result['username'])  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #
  #     # creates a <div> tag for each element in data
  #     # will print:
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
#
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another')
def another():
  return render_template("anotherfile.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print name
  cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
  g.conn.execute(text(cmd), name1 = name, name2 = name);
  return redirect('/')

# users pages
@app.route('/users')
def users():
    cursor = g.conn.execute("SELECT username FROM users")
    users = []
    for result in cursor:
      users.append(result['username'])  # can also be accessed using result[0]
    cursor.close()

    context = dict(data = users)
    return render_template("usersfile.html", **context)

# user page
@app.route('/users/<uid>')
def user(uid):
    league_cursor = g.conn.execute("SELECT l.lname, l.lid FROM leagues l JOIN participate p ON l.lid = p.lid where username = %s ", uid)
    leagues = []
    for result in league_cursor:
        leagues.append(result)
    league_cursor.close()
    #for league in leagues:


    context = dict(leagues= leagues, username = uid)
    return render_template("user.html", **context)

# roster page
@app.route('/rosters/<lid>/<uid>')
def roster(lid, uid):
    roster_cursor = g.conn.execute("SELECT p.name, p.pid FROM real_life_player_own p JOIN draft d ON d.pid = p.pid WHERE d.username = %s AND d.lid= %s", (uid, lid))
    roster = []
    for result in roster_cursor:
        roster.append(result)
    roster_cursor.close()

    lname_cursor = g.conn.execute("SELECT DISTINCT lname FROM leagues WHERE lid = %s", lid)
    lname = 0
    for result in lname_cursor:
        lname = result[0]
        break
    lname_cursor.close()
    context = dict(roster = roster, uid = uid, lname = lname)
    return render_template("roster.html", **context)

@app.route('/login')
def login():
    return another()
    #return render_template("anotherfile.html")

@app.route('/players/')
def players():
    cursor = g.conn.execute("SELECT p.name, s.pid, c.name, c.cid, count(s.pid) FROM real_life_player_own p JOIN score s ON p.pid = s.pid JOIN clubs c ON c.cid = p.cid GROUP BY (p.name, s.pid, c.name, c.cid) ORDER BY count DESC LIMIT 10");
    players = []
    for result in cursor:
        players.append(result)
    cursor.close()

    context = dict(data = players)
    return render_template("playersfile.html", **context)

@app.route('/players/<pid>')
def player(pid):
    p_cursor = g.conn.execute("SELECT p.name, c.name, c.cid, sum(score.ngoals) FROM real_life_player_own p JOIN score ON p.pid = score.pid JOIN clubs c ON p.cid=c.cid WHERE p.pid=%s GROUP BY c.cid, p.pid", pid)
    data = []
    for result in p_cursor:
        data.append(result)
    p_cursor.close()
    if data == []:
        cursor = g.conn.execute("SELECT p.name, c.name, c.cid, 0 FROM real_life_player_own p JOIN clubs c ON p.cid = c.cid WHERE p.pid=%s", pid)
        for result in cursor:
            data.append(result)
            break
        cursor.close()

    cursor2 = g.conn.execute("SELECT d.username, l.lname from draft d join real_life_player_own r on d.pid = r.pid join leagues l on l.lid = d.lid where r.pid =%s", pid)
    data2 = []
    for result in cursor2:
        data2.append(result)
    cursor2.close()

    context = dict(data=data, data2 = data2)
    return render_template("player.html", **context)

@app.route('/clubs/')
def clubs():
    cursor = g.conn.execute("SELECT name FROM clubs")
    clubs = []
    for result in cursor:
        clubs.append(result)
    cursor.close()

    context = dict(data = clubs)
    return render_template("clubsfile.html", **context)

@app.route('/clubs/<cid>')
def club(cid):
    cursor = g.conn.execute("SELECT p.name, sum(score.ngoals) FROM real_life_player_own p JOIN score ON p.pid = score.pid WHERE p.cid=%s GROUP BY p.pid", cid)
    players = []
    name = []
    for result in cursor:
        players.append(result)
        name.append(result[0])
    cursor.close()

    cursor1 = g.conn.execute("SELECT p.name from real_life_player_own p where p.cid=%s", cid)
    for result in cursor1:
        if result[0] not in name:
            name.append(result[0])
            players.append([result[0], 0])


    cursor2 = g.conn.execute("SELECT c1.name, c1.cid, c2.name, c2.cid, m.hteamgoals, m.ateamgoals FROM play_real_life_match m JOIN clubs c1 ON c1.cid = m.cid_h JOIN clubs c2 ON c2.cid = m.cid_a JOIN real_life_matchday rmd ON m.rmdid = rmd.rmdid WHERE (c1.cid = %s OR c2.cid = %s) ORDER BY m.rmdid", cid, cid)
    matches = []
    for result in cursor2:
        matches.append(result)
    cursor2.close()

    cursor3 = g.conn.execute("SELECT name FROM clubs WHERE cid=%s", cid)
    for result in cursor3:
        c_name = result[0]

    context = dict(p_data=players, m_data=matches, c_name=c_name)
    return render_template("club.html", **context)


@app.route('/leagues/')
def leagues():
    cursor = g.conn.execute("SELECT lname, lid FROM leagues")
    leagues = []
    for result in cursor:
        leagues.append(result)
    cursor.close()



    context = dict(data = leagues)
    return render_template("leaguesfile.html", **context)

@app.route('/leagues/<lid>')
def league(lid):

    lname_cursor = g.conn.execute("SELECT DISTINCT lname FROM leagues WHERE lid = %s", lid)
    lname = 0
    for result in lname_cursor:
        lname = result[0]
        break
    lname_cursor.close()

    user_cursor = g.conn.execute("SELECT username FROM participate WHERE lid = %s", lid)
    users = []
    for result in user_cursor:
        users.append(result[0])
    user_cursor.close()

    for i in range(len(users)):
        victories = count_victories(lid, users[i])
        draws = count_draws(lid, users[i])
        defeats = count_defeats(lid, users[i])
        points = 3 * victories + draws

        users[i].append(victories)
        users[i].append(draws)
        users[i].append(defeats)
        users[i].append(points)




    context = dict(users = users, lname=lname)
    return render_template("league.html", **context)


def count_victories(lid, uid):
    cursor = g.conn.execute("SELECT count(*) n_wins FROM ((SELECT p.fmid FROM play_fantasy_match p JOIN fantasy_matchdays f ON p.fmdid = f.fmdid WHERE p.username_h = %s AND F.lid = %s AND p.hteamgoals > p.ateamgoals) UNION (SELECT p.fmdid FROM play_fantasy_match p JOIN fantasy_matchdays f ON p.fmdid = f.fmdid WHERE p.username_a = %s AND F.lid = %s AND p.hteamgoals < p.ateamgoals)) as tmp", (uid, lid, uid, lid))
    victories = 0
    for result in cursor:
        victories = result[0]
        break
    return victories

def count_draws(lid, uid):
    cursor = g.conn.execute("SELECT count(*) n_wins FROM ((SELECT p.fmid FROM play_fantasy_match p JOIN fantasy_matchdays f ON p.fmdid = f.fmdid WHERE p.username_h = %s AND F.lid = %s AND p.hteamgoals = p.ateamgoals) UNION (SELECT p.fmdid FROM play_fantasy_match p JOIN fantasy_matchdays f ON p.fmdid = f.fmdid WHERE p.username_a = %s AND F.lid = %s AND p.hteamgoals = p.ateamgoals)) as tmp", (uid, lid, uid, lid))
    draws = 0
    for result in cursor:
        draws = result[0]
        break
    return draws

def count_defeats(lid, uid):
    cursor = g.conn.execute("SELECT count(*) n_wins FROM ((SELECT p.fmid FROM play_fantasy_match p JOIN fantasy_matchdays f ON p.fmdid = f.fmdid WHERE p.username_h = %s AND F.lid = %s AND p.hteamgoals < p.ateamgoals) UNION (SELECT p.fmdid FROM play_fantasy_match p JOIN fantasy_matchdays f ON p.fmdid = f.fmdid WHERE p.username_a = %s AND F.lid = %s AND p.hteamgoals > p.ateamgoals)) as tmp", (uid, lid, uid, lid))
    defeats = 0
    for result in cursor:
        defeats = result[0]
        break
    return defeats

def count_games(lid, uid):
    cursor = g.conn.execute("SELECT count(*) n_wins FROM ((SELECT p.fmid FROM play_fantasy_match p JOIN fantasy_matchdays f ON p.fmdid = f.fmdid WHERE p.username_h = %s AND F.lid = %s) UNION (SELECT p.fmdid FROM play_fantasy_match p JOIN fantasy_matchdays f ON p.fmdid = f.fmdid WHERE p.username_a = %s AND f.lid =%s)) as tmp", (uid, lid, uid, lid))
    games = 0
    for result in cursor:
        games = result[0]
        break
    return games

@app.route('/rlmatches/')
def rlmatches():
    cursor = g.conn.execute("SELECT DISTINCT rmdid FROM play_real_life_match ORDER BY rmdid ASC")
    rlmatchdays = []
    for result in cursor:
        rlmatchdays.append(result)
    cursor.close()
    rlmatches = []
    for i in range(len(rlmatchdays)):
        rlmatches.append([rlmatchdays[i][0]])
        rlmatches[i].append([])
        cursor = g.conn.execute("SELECT c1.name, c1.cid, c2.name, c2.cid, m.hteamgoals, m.ateamgoals FROM play_real_life_match m JOIN clubs c1 ON c1.cid = m.cid_h JOIN clubs c2 ON c2.cid = m.cid_a  WHERE rmdid = %s", rlmatchdays[i][0])
        for result in cursor:
            rlmatches[i][1].append(result)
        cursor.close()

    context = dict(data = rlmatches)
    return render_template("rlmatchesfile.html", **context)


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using
        python server.py
    Show the help text using
        python server.py --help
    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
