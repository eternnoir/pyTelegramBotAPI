#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This is an example echo bot using webhook with Twisted network framework.
# Updates are received with Twisted web server and processed in reactor thread pool.
# Relevant docs:
# https://twistedmatrix.com/documents/current/core/howto/reactor-basics.html
# https://twistedmatrix.com/documents/current/web/howto/using-twistedweb.html

import logging
import telebot
import json
from twisted.internet import ssl, reactor
from twisted.web.resource import Resource, ErrorPage
from twisted.web.server import Site, Request

API_TOKEN = '<api_token>'

WEBHOOK_HOST = '<ip or hostname>'
WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(API_TOKEN)

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(API_TOKEN)


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message,
                 ("Hi there, I am EchoBot.\n"
                  "I am here to echo your kind words back to you."))


# Handle all other messages
@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message, message.text)


# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))


# Process webhook calls
class WebhookHandler(Resource):
    isLeaf = True
    def render_POST(self, request: Request):
        request_body_dict = json.load(request.content)
        update = telebot.types.Update.de_json(request_body_dict)
        reactor.callInThread(lambda: bot.process_new_updates([update]))
        return b''


root = ErrorPage(403, 'Forbidden', '')
root.putChild(API_TOKEN.encode(), WebhookHandler())
site = Site(root)
sslcontext = ssl.DefaultOpenSSLContextFactory(WEBHOOK_SSL_PRIV, WEBHOOK_SSL_CERT)
reactor.listenSSL(8443, site, sslcontext)
reactor.run()
