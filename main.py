import web

urls = (
  '/', 'index',
  '/favicon.ico', 'icon'
)


class index:
  def GET(self):
    return "Hello, world!"


class icon:
  def GET(self):
    raise web.seeother("/static/favicon.ico")


if __name__ == "__main__":
  app = web.application(urls, globals())
  app.run()
