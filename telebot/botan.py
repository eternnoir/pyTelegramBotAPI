# -*- coding: utf-8 -*-

import requests
import json

import telebot

logger = telebot.logger


def track_event(token, event_name, user_id, event_description={}):
    if token is None:
        return False
    url = 'https://api.botan.io/track?token={token}&uid={user_id}&name={event_name}'.format(
        token=token,
        user_id=user_id,
        event_name=event_name,
    )
    request = requests.post(url, data=json.dumps(event_description), headers={'Content-Type': 'application/json'})
    try:
        response = request.json()
        return response['status'] == 'accepted'
    except Exception as e:
        logger.error('Failed to track event: {}'.format(e))
        return False
