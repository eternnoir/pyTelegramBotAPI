#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This example shows webhook echo bot with Tornado web framework
# Documenation to Tornado: http://tornadoweb.org

import signal

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

import telebot

API_TOKEN = '<api_token>'
WEBHOOK_CERT = "./cert.pem"
WEBHOOK_PKEY = "./pkey.pem"
WEBHOOK_HOST = "<domain_or_ip>"
WEBHOOK_SECRET = "<secret_uri_for_updates"
WEBHOOK_PORT = 88
WEBHOOK_URL_BASE = "https://{0}:{1}/{2}".format(WEBHOOK_HOST, str(WEBHOOK_PORT), WEBHOOK_SECRET)

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out pkey.pem 2048
# openssl req -new -x509 -days 3650 -key pkey.pem -out cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

bot = telebot.TeleBot(API_TOKEN)


class Root(tornado.web.RequestHandler):
    def get(self):
        self.write("Hi! This is webhook example!")
        self.finish()


class webhook_serv(tornado.web.RequestHandler):
    def get(self):
        self.write("What are you doing here?")
        self.finish()

    def post(self):
        if "Content-Length" in self.request.headers and \
            "Content-Type" in self.request.headers and \
            self.request.headers['Content-Type'] == "application/json":

            # length = int(self.request.headers['Content-Length'])
            json_data = self.request.body.decode("utf-8")
            update = telebot.types.Update.de_json(json_data)
            bot.process_new_updates([update])
            self.write("")
            self.finish()
        else:
            self.write("What are you doing here?")
            self.finish()


tornado.options.define("port", default=WEBHOOK_PORT, help="run on the given port", type=int)
is_closing = False


def signal_handler(signum, frame):
    global is_closing
    print("Exiting...")
    is_closing = True


def try_exit():
    global is_closing
    if is_closing:
        # clean up here
        tornado.ioloop.IOLoop.instance().stop()
        print("Exit success!")


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message,
                 ("Hi there, I am EchoBot.\n"
                  "I am here to echo your kind words back to you."))


bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE,
                certificate=open(WEBHOOK_CERT, 'r'))
tornado.options.options.logging = None
tornado.options.parse_command_line()
signal.signal(signal.SIGINT, signal_handler)
application = tornado.web.Application([
    (r"/", Root),
    (r"/" + WEBHOOK_SECRET, webhook_serv)
])

http_server = tornado.httpserver.HTTPServer(application, ssl_options={
    "certfile": WEBHOOK_CERT,
    "keyfile" : WEBHOOK_PKEY,
})
http_server.listen(tornado.options.options.port)
tornado.ioloop.PeriodicCallback(try_exit, 100).start()
tornado.ioloop.IOLoop.instance().start()
