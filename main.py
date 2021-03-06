from flask import Flask, g, request
import os
import psycopg2
import urllib
import urllib2
import urlparse
import onetimepass as otp
import time
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
import binascii


app = Flask(__name__)
STATUS_OK = 200
STATUS_BAD_REQUEST = 400
STATUS_INTERNAL_ERROR = 500


@app.route('/authenticate', methods=['POST'])
def authenticate():
  # Get request data
  auth_id = request.form.get('uid', None)
  auth_otp = request.form.get('otp', None)
  auth_token = request.form.get('token', None)
  auth_url = request.form.get('url', None)
  log("Request data:   "+str(request.form))
  if auth_id is None or auth_otp is None or auth_token is None or auth_url is None:
    log('Invalid request -> '+str(STATUS_BAD_REQUEST))
    return 'Invalid request', STATUS_BAD_REQUEST

  conn = g.db_conn
  cur = g.db_cur

  # Search for device in database
  cur.execute('SELECT id, uses, secret, last_used FROM devices WHERE id=%s', (auth_id,))
  rows = cur.fetchall()
  
  auth_trust = 0
  if len(rows) == 0:
    log('Invalid device')
  else:
    # Get info
    auth_uses = int(rows[0][1])
    auth_secret = str(rows[0][2])
    auth_lastused = int(rows[0][3])
    auth_otp = int(auth_otp)

    # Verify request using time-based one-time-password
    is_valid = False
    try:
      if not otp._is_possible_token(auth_otp, 6):
        log('Invalid token')
      else:
        # Accept OTPs from current, previous, and next 30 second intervals
        interval_now = int(time.time()) // 30
        otp_now = otp.get_hotp(auth_secret, interval_now)
        otp_prev = otp.get_hotp(auth_secret, interval_now - 1)
        otp_next = otp.get_hotp(auth_secret, interval_now + 1)
        log('Correct otp: ' + str([otp_prev, otp_now, otp_next]))
        if auth_otp == otp_now or auth_otp == otp_prev or auth_otp == otp_next:
          is_valid = True
    except TypeError:
      log('Invalid token')
      is_valid = False
    if not is_valid:
      log('Incorrect token')
    else:
      # Check for robotic device abuse (simplistic)
      time_now = int(time.time())
      secs_since_last_use = time_now - auth_lastused
      log("Time since last: " + str(secs_since_last_use))

      if secs_since_last_use < 10:
        # Rejection
        log('Robot detected; reject request')
        cur.execute('UPDATE devices SET last_used=%s WHERE id=%s', (time_now, auth_id))
        conn.commit()
      else:
        # Update device trust
        auth_uses += 1
        cur.execute('UPDATE devices SET uses=%s, last_used=%s WHERE id=%s', (auth_uses, time_now, auth_id))
        conn.commit()

        auth_trust = calculate_trust(auth_uses)

  # Send request info to remote URL
  if auth_trust > 0:
    log('sending ' + str(auth_trust) + ' trust to remote server')
    success = send_to_remote(auth_url, auth_token, auth_trust)
  else:
    log('ignored request due to 0 trust')
    success = True
  if not success:
    return 'Could not send to remote', STATUS_INTERNAL_ERROR

  # Indicate success
  log('Success -> '+str(STATUS_OK))
  return 'Success', STATUS_OK


@app.route('/register', methods=['POST'])
def register():
  # Get request data
  auth_id = request.form.get('uid', None)
  auth_secret = request.form.get('secret', None)
  log("Request data:   "+str(request.form))
  if auth_id is None or auth_secret is None:
    log('Invalid request -> '+str(STATUS_BAD_REQUEST))
    return 'Invalid request', STATUS_BAD_REQUEST

  conn = g.db_conn
  cur = g.db_cur

  # Insert new device
  try:
    cur.execute("INSERT INTO devices (id, uses, secret) VALUES (%s, %s, %s)", (auth_id, 0, auth_secret))
  except psycopg2.IntegrityError:
    log('Device already exists -> '+str(STATUS_BAD_REQUEST))
    return 'Device already exists', STATUS_BAD_REQUEST
  except Exception as e:
    log(str(e))
    return 'Internal error', STATUS_INTERNAL_ERROR
  conn.commit()

  # Indicate success
  log('Success -> '+str(STATUS_OK))
  return 'Success', STATUS_OK


@app.before_request
def before_request():
  # Get connection to database for this request or die
  g.db_conn = get_db_connection()
  if g.db_conn is None:
    log('Failed to connect to db -> '+str(STATUS_INTERNAL_ERROR))
    abort(STATUS_INTERNAL_ERROR)
  g.db_cur = g.db_conn.cursor()


@app.teardown_request
def teardown_request(exception):
  # Close connection to database for this request
  if hasattr(g, 'db_cur') and g.db_cur is not None:
    g.db_cur.close()
  if hasattr(g, 'db_conn') and g.db_conn is not None:
    g.db_conn.close()


def calculate_trust(auth_uses):
  # TODO: update trust algorithm
  return max(100 - auth_uses, 0)


def send_to_remote(auth_url, auth_token, auth_trust):
  signer = PKCS1_v1_5.new(app.config['private_key'])
  token_hash = SHA256.new(auth_token)
  token_sig_b64 = signer.sign(token_hash)
  token_sig_hex = binascii.hexlify(token_sig_b64)

  args = {'token':auth_token,
          'trust':auth_trust,
          'sig':token_sig_hex}
  data = urllib.urlencode(args)
  try:
    request = urllib2.Request(auth_url, data)
    response = urllib2.urlopen(request)
  except urllib2.HTTPError as e:
    log('HTTPError '+str(e.code)+': '+str(e.reason))
  except Exception as e:
    log(str(e))
    return False

  return True


def log(info):
  print info


def get_cryto_configuration():
  private_key = os.environ.get('PRIVATE_KEY', None)
  if private_key is None:
    log('PRIVATE_KEY environment variable not found')
    return None
  return {'private_key': private_key.replace('\\n', '\n')}


def get_db_configuration():
  urlparse.uses_netloc.append('postgres')
  db_url = os.environ.get('DATABASE_URL', None)
  if db_url is None:
    log('DATABASE_URL environment variable not found')
    return None
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
    log('Database error -> '+str(e.pgcode)+" -> "+e.pgerror)
  except Exception as e:
    db_conn = None
    log(str(e))
  return db_conn


def get_port():
  port = int(os.environ.get("PORT", 8080))
  return port


if __name__ == "__main__":
  db_info = get_db_configuration()
  if db_info is None:
    exit()
  else:
    app.config['db_user'] = db_info['username']
    app.config['db_pword'] = db_info['password']
    app.config['db_host'] = db_info['hostname']
    app.config['db_name'] = db_info['database']

  crypto_info = get_cryto_configuration()
  if crypto_info is None:
    exit()
  else:
    app.config['private_key'] = RSA.importKey(crypto_info['private_key'])

  app.config['DEBUG'] = True

  app.run(host='0.0.0.0', port=get_port())
