from flask import Flask, g, request
import os
import psycopg2
import urlparse

app = Flask(__name__)


@app.route('/authenticate', methods=['POST'])
def authenticate():
  # Get request data
  auth_id = request.form.get('id', None)
  auth_token = request.form.get('token', None)
  auth_url = request.form.get('url', None)
  if auth_id is None or auth_token is None or auth_url is None:
    return 'Bad request'

  conn = g.db_conn
  cur = g.db_cur

  # Search for device in database
  cur.execute('SELECT uses FROM devices WHERE id=%s', (auth_id))
  rows = cur.fetchall()
  if len(rows) == 0:
    return 'Device not found'

  # Update device trust
  auth_uses = rows[0][0]
  auth_uses += 1
  cur.execute('UPDATE devices SET uses=%s WHERE id=%s', (auth_uses, auth_id))
  conn.commit()

  # Send request info to remote URL
  success = send_to_remote(auth_url, auth_token, auth_uses)
  if not success:
    return 'Could not send to remote'

  # Indicate success
  return 'Success'


@app.route('/register', methods=['POST'])
def register():
  # Get request data
  auth_id = request.form.get('id', None)
  if auth_id is None:
    return 'Bad request'

  conn = g.db_conn
  cur = g.db_cur

  # Ensure device does not already exist
  cur.execute('SELECT * FROM devices WHERE id=%s', (auth_id))
  rows = cur.fetchall()
  if len(rows) != 0:
    return 'Device already exists'

  # Insert new device
  try:
    cur.execute("INSERT INTO devices (id, uses) VALUES (%s, %s)", (auth_id, 0))
  except psycopg2.IntegrityError:
    return 'Device already exists'
  conn.commit()

  # Indicate success
  return 'Success'


@app.before_request
def before_request():
  # Get connection to database for this request or die
  g.db_conn = get_db_connection()
  if g.db_conn is None:
    abort(500)
  g.db_cur = g.db_conn.cursor()


@app.teardown_request
def teardown_request(exception):
  # Close connection to database for this request
  if hasattr(g, 'db_cur') and g.db_cur is not None:
    g.db_cur.close()
  if hasattr(g, 'db_conn') and g.db_conn is not None:
    g.db_conn.close()


def send_to_remote(auth_url, auth_token, auth_uses):
  # TODO
  return True


def get_db_configuration():
  urlparse.uses_netloc.append('postgres')
  db_url = os.environ.get('DATABASE_URL', None)
  if db_url is None:
    print 'DATABASE_URL environment variable not found'
    print 'Exiting...'
    return
  url = urlparse.urlparse(os.environ['DATABASE_URL'])

  return {'username': url.username,
          'password': url.password,
          'hostname': url.hostname,
          'database': url.path[1:]}


def get_db_connection():
  try:
    db_conn = psycopg2.connect(dbname=app.config['db_name'],
                               user=app.config['db_user'],
                               password=app.config['db_pword'],
                               host=app.config['db_host'])
  except psycopg2.Error as e:
    db_conn = None
    print "Database error %s: %s", (e.pgcode, e.pgerror)
  return db_conn



def get_port():
  port = int(os.environ.get("PORT", 8080))
  return port


if __name__ == "__main__":
  db_info = get_db_configuration()
  app.config['db_user'] = db_info['username']
  app.config['db_pword'] = db_info['password']
  app.config['db_host'] = db_info['hostname']
  app.config['db_name'] = db_info['database']

  app.config['DEBUG'] = True

  app.run(host='0.0.0.0', port=get_port())
