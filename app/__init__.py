#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from os.path import dirname
from os.path import join
from flask import Flask

app = Flask(__name__)
app.template_folder = join(dirname(__file__), 'templates')
app.static_folder = join(dirname(__file__), 'static')


class UserConfig(dict):
    """ loads the json configuration file """

    def _string_decode_hook(self, data):
        rv = {}
        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            rv[key] = value
        return rv

    def __init__(self):
        dict.__init__(self)
        configfile = join(dirname(dirname(__file__)), 'config.json')
        self.update(json.load(open(configfile), object_hook=self._string_decode_hook))

app.config['USER_CONFIG'] = UserConfig()

# only load influxdb endpoint if module is available
try:
    import influxdb
except ImportError:
    # remove influxdb config because we can't use it
    if 'influxdb' in app.config['USER_CONFIG']:
        del app.config['USER_CONFIG']['influxdb']

    # log something so the user knows what's up
    # TODO: make logging work!
    app.logger.warning('No influxdb module found, disabling influxdb support')
else:
    # only load endpoint if user wants to use influxdb
    if 'influxdb' in app.config['USER_CONFIG']:
        from app.influx.views import InfluxResource
        app.register_blueprint(InfluxResource.as_blueprint())

# only load endpoint if user wants to use graphite
if 'graphite' in app.config['USER_CONFIG']:
    from app.graphite.views import GraphiteResource
    app.register_blueprint(GraphiteResource.as_blueprint())

# load dashboard and graphite endpoint
from app.dashboard.views import DashboardResource
app.register_blueprint(DashboardResource.as_blueprint())

from app.pool.views import PoolsResource
app.register_blueprint(PoolsResource.as_blueprint())

from app.snap.views import SnapsResource
app.register_blueprint(SnapsResource.as_blueprint())

from app.object.views import ObjectsResource
app.register_blueprint(ObjectsResource.as_blueprint())

from app.image.views import ImagesResource
app.register_blueprint(ImagesResource.as_blueprint()) 

from app.image.views import ImageResource
app.register_blueprint(ImageResource.as_blueprint())

from app.disk.views import DisksResource
app.register_blueprint(DisksResource.as_blueprint())

from app.mds.views import MDSResource
app.register_blueprint(MDSResource.as_blueprint())



#print app.url_map
