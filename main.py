#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os,logging
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch
from xml.dom.minidom import Document
from xml.dom.minidom import parseString
from google.appengine.ext.webapp import template
from disqusapi import DisqusAPI,APIError



TEMPLATE_DIR='tmplt/'
INDEX_TILE='index_tile.html'

DOMAIN="appspot.com"
PATH="api?method=photo.one&gkey"
GRAPH= "http://graph.facebook.com/"

DISQUS_SECRET_KEY="ipy3BcoJZhntJ3HT6rdT5OKsr6hVByiABIQ0dKFmDCfOM6neWgcyL27lziVS5GNh"

class Content(db.Model):
    appname = db.StringProperty()
    gkey = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now_add=True)
    title = db.StringProperty()
    tags = db.ListProperty(db.Category)
    rate = db.RatingProperty()
    thumbnail = db.LinkProperty()
    instax = db.LinkProperty()
    origimg = db.LinkProperty()
    fb_id = db.StringProperty()
    def update_info(self):
        url = "http://%s.%s/%s=%s"%(self.appname,DOMAIN,PATH,self.gkey)
        logging.debug(url)
        result = urlfetch.fetch(url)

        if result.status_code == 200:
            dom = parseString(result.content)
            logging.debug(result.content)
            self.fb_id = dom.getElementsByTagName('fb_id')[0].childNodes[0].data
            self.thumbnail = dom.getElementsByTagName('small')[0].childNodes[0].data
            self.instax = dom.getElementsByTagName('medium')[0].childNodes[0].data
            self.origimg = dom.getElementsByTagName('big')[0].childNodes[0].data
            self.put()
            
def photolog_list_all(keyword='',limit=5):
    if keyword:
        ctt_query = Content.all().order('-timestamp').filter("tags",keyword)
    else:
        ctt_query = Content.all().order('-timestamp')

    contents = ctt_query.fetch(limit)
#    cursor = ctt_query.cursor()
#    memcache.set('plist_cursor', cursor)
    
    return contents

def get_comment():
    disqus = DisqusAPI(DISQUS_SECRET_KEY)
    list = disqus.trends.listThreads()
    logging.debug(list)
    
    
class MainHandler(webapp.RequestHandler):
    def get(self):
        obj_contents = photolog_list_all(None,10)
#        get_comment()
        template_values = {
            'obj_contents' : obj_contents
        }
        path = os.path.join(os.path.dirname(__file__),TEMPLATE_DIR,INDEX_TILE)
        self.response.out.write(template.render(path, template_values).decode('utf-8'))

class RunPost(webapp.RequestHandler):
    def post(self):
        logging.debug(self.request)
        newPost = Content()
        newPost.appname = self.request.get('appname')
        newPost.gkey = self.request.get('gkey')
        newPost.put()
        newPost.update_info()
        
def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication(
                                         [
                                          ('/', MainHandler),
                                          ('/post_to_gp',RunPost)
                                          ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
