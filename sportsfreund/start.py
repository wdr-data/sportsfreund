#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging

os.environ["DJANGO_SETTINGS_MODULE"] = "sportsfreund.settings"

import cherrypy
import django
django.setup()

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from paste.translogger import TransLogger


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


class SportsfreundApplication(object):
    HOST = "127.0.0.1"
    PORT = 8000

    def mount_static(self, url, root):
        """
        :param url: Relative url
        :param root: Path to static files root
        """
        config = {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': root,
            'tools.expires.on': True,
            'tools.expires.secs': 86400
        }
        cherrypy.tree.mount(None, url, {'/': config})

    def run(self):
        cherrypy.config.update({
            'environment': 'production',
            'server.socket_host': self.HOST,
            'server.socket_port': self.PORT,
            'engine.autoreload_on': False,
            'log.error_file': 'site.log',
            'log.screen': True
        })
        self.mount_static(settings.STATIC_URL, settings.STATIC_ROOT)

        cherrypy.log("Loading and serving Django application on %s" % settings.URL_PREFIX)
        cherrypy.tree.graft(TransLogger(WSGIHandler()), settings.URL_PREFIX)
        cherrypy.engine.start()
        cherrypy.log("Your app is running at http://%s:%s" % (self.HOST, self.PORT))

        cherrypy.engine.block()


if __name__ == "__main__":
    SportsfreundApplication().run()
