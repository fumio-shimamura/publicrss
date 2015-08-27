#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import os
import datetime
import logging
from google.appengine.dist import use_library
use_library('django', '1.2')
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util


class Feedsite(db.Model):
    sitename = db.StringProperty(required=True)
    siteurl     = db.StringProperty(required=True)
    sitetime  = db.DateTimeProperty(auto_now_add=True)


def parse_feed(feed_url):
    import feedparser
    from google.appengine.api import urlfetch
    """
    call feedpaser module
    """
    result = urlfetch.fetch(feed_url)
    if result.status_code == 200:
        d = feedparser.parse(result.content)
    else:
        raise Exception('Can not retrieve giben URL.')
    if d.bozo == 1:
        raise Exception('Can not parse giben URL.')
    return d


class HeadHandler(webapp.RequestHandler):
    def get(self):
# display feedsite information
        feedsite  = db.GqlQuery(
            'SELECT * FROM Feedsite '
            'ORDER BY sitetime')
        template_values = {
            'tp_feed': feedsite
            }
        path = os.path.join(os.path.dirname(__file__), 
                                       'template/publicrss.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
# add feedsite information
        if self.request.get('add_site') !='':
            if (self.request.get('t_sitename') !='' and 
                self.request.get('t_siteurl') !='' ):
                feedsite = Feedsite(
                    sitename = self.request.get('t_sitename'),
                    siteurl = self.request.get('t_siteurl'))
                feedsite.put( )
            self.redirect('/publicrss')
# delete feedsite information
        if self.request.get('del_site') !='':
            for feedsite in Feedsite.all( ):
                if self.request.get(str(feedsite.siteurl))  !='':
                    feedsite.delete( )
            self.redirect('/publicrss')
# set feedsite URL to Cookie
        if self.request.get('get_item') !='':
            cookie = 'publicrss_siteurl=%s;' % self.request.get('get_item')
            self.response.headers.add_header('Set-Cookie', cookie )
            self.redirect('/publicrss/item')


class ItemHandler(webapp.RequestHandler):
    def get(self):
# get feedsite URL from Cookie
        feedsiteurl= self.request.cookies.get('publicrss_siteurl', '')
# get feed
        try:
            d = parse_feed(feedsiteurl)
        except Exception, e:
            logging.info(Exception)
            return self.redirect('/publicrss?error=Invalid%20URL')
# display feed
        template_values = {
            'tp_feed':d.feed ,
            'tp_feeditem':d.entries
            }
        path = os.path.join(os.path.dirname(__file__), 
                                       'template/publicrssitem.html')
        self.response.out.write(template.render(path, template_values))


def main():
    application = webapp.WSGIApplication(
                                         [('/publicrss', HeadHandler),
                                          ('/publicrss/item', ItemHandler)],
                                         debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
