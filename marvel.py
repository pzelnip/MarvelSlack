from collections import namedtuple
from ConfigParser import RawConfigParser
from hashlib import md5
import json
import os
import random
import sys 
import time
import urllib 

from flask import Flask
from flask import request
import requests


app = Flask(__name__)


class CONFIG(object):
    def __init__(self):
        pass

    @classmethod
    def get(cls, value):
        return os.environ[value]


def parse_marvel_entry(result):
    entry = {
        'description' : "No description available",
        'wiki' : "No wiki available",
        'thumbnail' : "No thumbnail available",
    }

    if result.has_key('description') and result['description']:
        entry['description'] = result['description']

    if result.has_key('urls') and len(result['urls']):
        urls = result['urls']

        for url in urls:
            if url['type'] == 'wiki':
                entry['wiki'] = url['url']

    if result.has_key('thumbnail') and result['thumbnail']:
        entry['thumbnail'] = result['thumbnail']['path'] + "." + result['thumbnail']['extension']

    return entry


def marvel(char):
    marvel_public_key = CONFIG.get('marvelPublicKey')
    marvel_private_key = CONFIG.get('marvelPrivateKey')

    timestamp = str(int(time.time()))
    hash_val = md5(timestamp + marvel_private_key + marvel_public_key).hexdigest()

    url = 'http://gateway.marvel.com:80/v1/public/characters?&apikey=' + marvel_public_key + '&ts=' + timestamp + '&hash=' + hash_val + '&name=' + char 

    headers = {'content-type':'application/json'}
    request = requests.get(url, headers=headers)
    if request.status_code == 200:
        data = json.loads(request.content)['data']
        results = data['results']
        if len(results):
            return (True, parse_marvel_entry(results[0]))
        else:
            #print "no info for " + char 
            return (False, "no info for " + char)
    else:
        return (False, "Error: " + request)


@app.route('/')
def hello():
    return "Hello world"


@app.route('/marvel/<char>')
def marvelchar(char):
    return json.dumps(marvel(char))

 
@app.route('/test')
def test():
    q = request.args
    (text, channel, user) = (
        q.get('text', ''),
        q.get('channel_name', ''),
        q.get('user_name', ''))

    (valid, result) = marvel(text)

    if not valid:
        return result

    text = """
%s requested info for: %s
Description: %s
Wiki: %s
Thumbnail: %s
""" % (user, text, result['description'], result['wiki'], result['thumbnail'])
    #post_to_slack(text, channel, "MarvelBot", result['thumbnail'])

    return text #""
    
    
def post_to_slack(text, channel, username, icon_url='http://fc05.deviantart.net/fs46/i/2009/188/1/d/Marvel_Comics_Dock_Icon_by_Meganubis.png'):
    url = CONFIG.get('slackWebHookURL')

    headers = {'content-type':'application/json'}
    payload = json.dumps({
            'channel' : "#" + channel,
            'username' : username,
            'text' : text,
            'icon_url' : icon_url, 
    })
    request = requests.post(url, headers=headers, 
        data=payload)
    print "POST: %s - %s" % (request.status_code, request.reason)
    

def main():
    app.run()


if __name__ == "__main__":
    main()
