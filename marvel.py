import urllib 
import random
import requests
import time
import json
import sys 
from hashlib import md5
from collections import namedtuple
from ConfigParser import RawConfigParser

from bottle import route, run, template, request, get, post

CONFIG_KEY = 'config'
CONFIG = None


def read_config(cfgfile):
    global CONFIG
    Config = namedtuple('config', ['host', 'port', 'marvelPublicKey', 'marvelPrivateKey', 'slackWebHookURL'])
    configp = RawConfigParser()    
    configp.read(cfgfile)
    CONFIG = Config(
        configp.get(CONFIG_KEY, 'host'),
        configp.get(CONFIG_KEY, 'port'),
        configp.get(CONFIG_KEY, 'marvelPublicKey'),
        configp.get(CONFIG_KEY, 'marvelPrivateKey'),
        configp.get(CONFIG_KEY, 'slackWebHookURL'),
    )


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
    marvel_public_key = CONFIG.marvelPublicKey 
    marvel_private_key = CONFIG.marvelPrivateKey 

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


@route('/marvel/<char>')
def index(char):
    return json.dumps(marvel(char))

 
@route('/test')
def index():
    q = request.query
    (text, channel, user) = (q['text'], q['channel_name'], q['user_name'])
    
    (valid, result) = marvel(text)

    if not valid:
        return result

    text = """
%s requested info for: %s
Description: %s
Wiki: %s
Thumbnail: %s
""" % (user, text, result['description'], result['wiki'], result['thumbnail'])
    post_to_slack(text, channel, "MarvelBot", result['thumbnail'])

    return ""
    
    
def post_to_slack(text, channel, username, icon_url='http://fc05.deviantart.net/fs46/i/2009/188/1/d/Marvel_Comics_Dock_Icon_by_Meganubis.png'):
    url = CONFIG.slackWebHookURL 

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
    

def bottle():
    run(host=CONFIG.host, port=CONFIG.port)


def main():
    read_config('config.cfg')
    print CONFIG 
    bottle()


if __name__ == "__main__":
    main()
