import urllib
import urllib2
import sys
import hashlib
import onetimepass
import random
import string
import sys


def main(argc, argv):
  usage = 'usage: python %s [register [local|remote] | authenticate [local|remote] uid secret token]' % argv[0]
  localURL = 'http://localhost:5000'
  remoteURL = 'http://eecs588-auth.herokuapp.com'
  targetURL = 'https://gotdevices.herokuapp.com/api/devicecheck'

  if argc < 3:
    print  usage
    exit()

  serverURL = ''
  if argv[2].lower() == 'local':
    serverURL = localURL
  elif argv[2].lower() == 'remote':
    serverURL = remoteURL
  else:
    print usage
    exit()

  if argv[1].lower() == 'register' and argc == 3:
    register(serverURL)
  elif argv[1].lower() == 'authenticate' and argc == 6:
    authenticate(serverURL, argv[3], argv[4], argv[5], targetURL)
  else:
    print usage
    exit()


def register(serverURL):
  random.seed()
  uid = random.randint(0, 99999999)
  secret = ''.join([random.choice(string.uppercase + '234567') for i in range(16)])
  deviceToken = onetimepass.get_totp(secret)

  print 'Device credentials: [' + str(uid) + ', ' + str(secret) + ']'
  args = {'uid':uid, 'secret':secret}
  sendRequest(serverURL + '/register', args)


def authenticate(serverURL, uid, secret, token, targetURL):
  try:
    otp = onetimepass.get_totp(secret)
  except TypeError as e:
    print 'Secret must be a multiple of 8 alphanumeric characters'
    exit()
  except Exception as e:
    print e
    return

  args = {'uid':uid,
          'otp':otp,
          'token':token,
          'url':targetURL}
  sendRequest(serverURL + '/authenticate', args)


def sendRequest(url, args):
  data = urllib.urlencode(args)
  request = urllib2.Request(url, data)
  try:
    response = urllib2.urlopen(request)
  except urllib2.HTTPError as e:
    print e
    return

  html = response.read()
  print html


if __name__ == '__main__' :
  main(len(sys.argv), sys.argv)
