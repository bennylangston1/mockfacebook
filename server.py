#!/usr/bin/python
"""mockfacebook is a mock HTTP server for the Facebook FQL and Graph APIs.

http://code.google.com/p/mockfacebook/

mockfacebook can be used in place of the live Facebook servers as an FQL and
Graph API endpoint. It supports the full FQL query language and all Graph API
endpoints except writing. It can download and uses data from live Facebook, or
you can enter your own data.

mockfacebook includes an automated utility that reads the Facebook developer
docs and example data, infers and stores the current FQL and Graph API schemas,
assists with building a schema mapping, and generates test data. This helps it
stay up to date in the face of Facebook's rapid iteration and API changes. (It's
also better than the Graph API's `?metadata=true`, which is often wrong or out
of date because it's written by hand, not auto-generated from the real schema.)

mockfacebook is backed by SQLite. It's single threaded, so it's not suitable for
load testing, high throughput, or performance. If you need any of that, try
http://www.friendrunner.com/ .

Depends on the sqlparse package: http://code.google.com/p/python-sqlparse/

Usage:
  server.py [--port PORT] [--me USER_ID] [--file SQLITE_DB_FILE]

Supported FQL features:
- almost all tables
- all functions: me(), now(), strlen(), substr(), strpos()
- indexable columns. returns an error if a non-indexable column is used in a
  WHERE clause.
- basic error codes and messages
- JSON and XML output formats

Supported Graph API features:
- almost all object and connection types
- basic object lookup
- aliases (e.g. /[username] for users)
- basic error messages and types
- multiple selection via ?ids=...

OAuth authentication is also supported, including auth codes, access tokens,
server and client side flows, and app login. Individual permission checking
is not supported yet.

Notes: 
- all datetime/unix timestamp values should be inserted into the database as UTC

Relevant links to mention in release announcement:
http://code.google.com/p/thefakebook/
http://www.testfacebook.com/
http://www.friendrunner.com/
https://github.com/arsduo/koala
http://groups.google.com/group/thinkupapp/browse_thread/thread/825ed3989d5eb164/686fd57e937ae109
http://developers.facebook.com/blog/post/429/


TODO:
- parallelize fql schema scrape http requests
- load test download
- require locale and either native_hash or pre_hash_string for translation table:
  file:///home/ryanb/docs/facebook_fql/translation/index.html
- query restrictions on unified_message and unified_thread

- insights
- the permissions table
- validate subselects
- more errors
- permissions
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import logging
import optparse
import sqlite3
import sys
import wsgiref.simple_server

import webapp2

import fql
import graph
import oauth

# how often the HTTP server should poll for shutdown, in seconds
SERVER_POLL_INTERVAL = 0.5

# optparse.Values object that holds command line options
options = None

# order matters here! the first handler with a matching route is used.
HANDLER_CLASSES = (
  oauth.AuthCodeHandler,
  oauth.AccessTokenHandler,
  fql.FqlHandler,
  graph.ObjectHandler,
  graph.ConnectionHandler,
  )


def application():
  """Returns the WSGIApplication to run.
  """
  routes = reduce(lambda x, y: x + y, [cls.ROUTES for cls in HANDLER_CLASSES])
  return webapp2.WSGIApplication(routes, debug=True)


def parse_args(argv):
  global options

  parser = optparse.OptionParser(
    description='mockfacebook is a mock HTTP server for the Facebook Graph API.')
  parser.add_option('-p', '--port', type='int', default=8000,
                    help='port to serve on (default 8000)')
  parser.add_option('-f', '--file', default= 'mockfacebook.db',
                    help='SQLite database file (default mockfacebook.db)')
  parser.add_option('--me', type='int', default=0,
                    help='user id that me() should return (default 0)')

  (options, args) = parser.parse_args(args=argv)
  logging.debug('Command line options: %s' % options)


def main(args, started=None):
  """Args:
    args: list of string command line arguments
    started: an Event to set once the server has started. for testing.
  """
  parse_args(args)
  print 'Options: %s' % options

  conn = sqlite3.connect(options.file)
  fql.FqlHandler.init(conn, options.me)
  graph.BaseHandler.init(conn, options.me)
  oauth.BaseHandler.init(conn)

  global server  # for server_test.ServerTest
  server = wsgiref.simple_server.make_server('', options.port, application())

  print 'Serving on port %d...' % options.port
  if started:
    started.set()
  server.serve_forever(poll_interval=SERVER_POLL_INTERVAL)


if __name__ == '__main__':
  main(sys.argv)
