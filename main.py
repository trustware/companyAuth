from flask import Flask
import os
import psycopg2
import urlparse
import sys


app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello world!"


def main(argc, argv):
  # Connect to SQL database
  urlparse.uses_netloc.append('postgres')
  if not os.environ.has_key('DATABASE_URL'):
    print 'DATABASE_URL environment variable not found'
    print 'Exiting...'
    return
  url = urlparse.urlparse(os.environ['DATABASE_URL'])
  try:
    conn = psycopg2.connect(dbname=url.path[1:], user=url.username,
        password=url.password, host=url.hostname)
  except psycopg2.Error as e:
    print 'Could not connect to database:', e.pgerror
    print 'Exiting...'
    return

  # Start accepting requests
  port = int(os.environ.get("PORT", 8080))
  app.run(host='0.0.0.0', port=port)


if __name__ == "__main__":
  main(len(sys.argv), sys.argv)
