import urllib
import urllib2
import sys


def main(argc, argv):
  if argc != 4:
    print 'usage: python %s [local|remote] [register|authenticate] deviceID' % argv[0]
    exit()

  server = argv[1].lower()
  task = argv[2].lower()

  deviceID = argv[3]
  one_time_password = 'abcdef'
  token = 'ghijkl'
  target_url = 'http://gotdevices.herokuapp.com/devicecheck'

  if server == 'local':
    trust_url = 'http://localhost:5000'
  elif server == 'remote':
    trust_url = 'http://eecs588-auth.herokuapp.com'
  else:
    print 'usage: python %s [local|remote] [register|authenticate] deviceID' % argv[0]
    exit()

  args = {}
  if task == 'register':
    trust_url += '/register'
    args = {'uid':deviceID}
  elif task == 'authenticate':
    trust_url += '/authenticate'
    args = {'uid':deviceID,
            'otp':one_time_password,
            'token':token,
            'url':target_url}
  else:
    print 'usage: python %s [local|remote] [register|authenticate] deviceID' % argv[0]
    exit()

  data = urllib.urlencode(args)
  request = urllib2.Request(trust_url, data)
  try:
    response = urllib2.urlopen(request)
  except urllib2.HTTPError as e:
    print e
    print e.read()
    return

  html = response.read()
  print html


if __name__ == '__main__' :
  main(len(sys.argv), sys.argv)
