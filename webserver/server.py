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

@app.route('/join_league/<uid>', methods=['POST'])
def join_league(uid):
  league = request.form['league']

  # need to know the lid of the knewly created league
  cursor = g.conn.execute("SELECT lid from leagues where lname =%s", league)
  for result in cursor:
      lid = result[0]

  # add to the participate table
  cmd = 'INSERT INTO participate(lid,username) VALUES (:lid,:uid)'
  g.conn.execute(text(cmd), lid=lid, uid=uid)

  return redirect('/users/%s' %(uid))

@app.route('/create_league/<uid>', methods=['POST'])
def create_league(uid):
  league = request.form['league']
  cmd = 'INSERT INTO leagues(lname) VALUES (:league)';
  g.conn.execute(text(cmd), league= league);

  # need to know the lid of the knewly created league
  cursor = g.conn.execute("SELECT lid from leagues where lname =%s", league)
  for result in cursor:
      lid = result[0]


  # add to the participate table
  cmd = 'INSERT INTO participate(lid,username) VALUES (:lid,:uid)'
  g.conn.execute(text(cmd), lid=lid, uid=uid)

  return redirect('/users/%s' %(uid))

@app.route('/draft/<lid>/<uid>', methods=['POST'])
def draft(lid, uid):
    player = request.form['player']

    # need to get back the pid of that player
    cursor = g.conn.execute("SELECT pid FROM real_life_player_own WHERE name=%s", player)
    for result in cursor:
        pid = result[0]

    # need to get back the lid of that league
    cursor = g.conn.execute("SELECT lid FROM leagues WHERE lname=%s", lid)
    for result in cursor:
        lid = result[0]

    # add the player to the roster
    cmd = 'INSERT INTO draft(lid, username, pid) VALUES (:lid, :uid, :pid)'
    g.conn.execute(text(cmd), lid=lid, uid=uid, pid=pid)
    return redirect('/rosters/%i/%s' %(lid,uid))

# users pages
@app.route('/users')
def users():
    cursor = g.conn.execute("SELECT username FROM users")
    users = []
    for result in cursor:
      users.append(result['username'])
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
    context = dict(roster = roster, uid = uid, lname = lname, lid = lid)
    return render_template("roster.html", **context)

@app.route('/login')
def login():
    return another()
    #return render_template("anotherfile.html")

@app.route('/players/')
def players():
    cursor = g.conn.execute("SELECT p.name, s.pid, c.name, c.cid, sum(s.ngoals) goals FROM real_life_player_own p JOIN score s ON p.pid = s.pid JOIN clubs c ON c.cid = p.cid GROUP BY (p.name, s.pid, c.name, c.cid) ORDER BY goals DESC LIMIT 10");
    players = []
    for result in cursor:
        players.append(result)
    cursor.close()

    context = dict(data = players)
    return render_template("playersfile.html", **context)

@app.route('/players/<pid>')
def player(pid):
    p_cursor = g.conn.execute("SELECT p.name, c.name, c.cid, COALESCE(sum(score.ngoals), 0) FROM real_life_player_own p LEFT JOIN score ON p.pid = score.pid JOIN clubs c ON p.cid=c.cid WHERE p.pid=%s GROUP BY c.cid, p.pid", pid)
    data = []
    for result in p_cursor:
        data.append(result)
    p_cursor.close()

    cursor2 = g.conn.execute("SELECT d.username, l.lname, l.lid from draft d join real_life_player_own r on d.pid = r.pid join leagues l on l.lid = d.lid where r.pid =%s", pid)
    data2 = []
    for result in cursor2:
        data2.append(result)
    cursor2.close()

    context = dict(data=data, data2 = data2)
    return render_template("player.html", **context)

@app.route('/get_player', methods=['POST'])
def get_player():
    name = request.form['name']

    cursor = g.conn.execute("SELECT pid FROM real_life_player_own WHERE name=%s", name)
    for result in cursor:
        pid = result[0]
    return player(pid)

@app.route('/clubs/')
def clubs():
    cursor = g.conn.execute("SELECT name, cid FROM clubs")
    clubs = []
    for result in cursor:
        clubs.append(result)
    cursor.close()

    context = dict(data = clubs)
    return render_template("clubsfile.html", **context)

@app.route('/clubs/<cid>')
def club(cid):
    cursor = g.conn.execute("SELECT p.name, p.pid, COALESCE(sum(score.ngoals), 0) goals FROM real_life_player_own p LEFT JOIN score ON p.pid = score.pid WHERE p.cid=%s GROUP BY p.pid ORDER BY goals desc", cid)
    players = []
    ids = []
    for result in cursor:
        players.append(result)
        ids.append(result[1])
    cursor.close()

    cursor1 = g.conn.execute("SELECT p.name, p.pid, 0 from real_life_player_own p where p.cid=%s", cid)
    for result in cursor1:
        if result[1] not in ids:
            ids.append(result[1])
            players.append(result)


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

    user_cursor = g.conn.execute("""WITH matches AS (SELECT * FROM play_fantasy_match p JOIN fantasy_matchdays f ON p.fmdid = f.fmdid WHERE f.lid = %s),
     wins AS(SELECT u.username, count(*) n_wins FROM users u, matches p  WHERE ((u.username = p.username_h AND p.hteamgoals > p.ateamgoals) OR (u.username = p.username_a AND p.hteamgoals < p.ateamgoals)) group by u.username),
     draws AS(SELECT u.username, count(*) n_draws FROM users u, matches p WHERE ((u.username = p.username_h AND p.hteamgoals = p.ateamgoals) OR (u.username = p.username_a AND p.hteamgoals = p.ateamgoals))group by u.username),
     losses AS (SELECT u.username, count (*) n_losses FROM users u, matches p WHERE((u.username = p.username_h AND p.hteamgoals < p.ateamgoals) OR(u.username = p.username_a AND p.hteamgoals > p.ateamgoals)) group by u.username),
     wdl AS(SELECT p.username usern, COALESCE(wins.n_wins,0) W, COALESCE(draws.n_draws, 0) D, COALESCE(losses.n_losses,0) L FROM participate p LEFT JOIN wins ON p.username = wins.username LEFT JOIN draws ON p.username = draws.username LEFT JOIN losses ON p.username = losses.username WHERE p.lid = %s),
     pts AS (SELECT usern, w, d, l, 3*w + d p FROM wdl) SELECT usern, w, d, l, p, RANK() OVER(ORDER BY p DESC) FROM pts;""", lid, lid)
    users = []
    for result in user_cursor:
        users.append(result)
    user_cursor.close()

    md_cursor = g.conn.execute("SELECT f.fmdid, c.rmdid FROM correspond_to c JOIN fantasy_matchdays f ON f.fmdid = c.fmdid WHERE f.lid = %s", lid)
    matchdays = []
    for result in md_cursor:
        matchdays.append(result)
    md_cursor.close()

    context = dict(lid = lid, users = users, lname=lname, matchdays = matchdays)
    return render_template("league.html", **context)

@app.route('/leagues/<lid>/<fmdid>')
def fmd(lid, fmdid):
    return(0)
#### TODO


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

## SQL request for getting a match result from a certain league, a certain matchday, and a certain couple of usernames
# with sc as (select ngoals, pid from score s join correspond_to c on s.rmdid = c.rmdid where fmdid = 1), goals as(select d.username, coalesce(sum(s.ngoals),0) goals from draft d left join sc s on d.pid = s.pid where d.lid = 1 group by d.username) select g1.username, g1.goals, g2.goals, g2.username from goals g1, goals g2 where g1.username = 'Arnaud' and g2.username = 'Redouane';

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
