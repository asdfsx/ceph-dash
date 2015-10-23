#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json

from flask import request
from flask import render_template
from flask import abort
from flask import redirect
from flask import url_for
from flask import jsonify
from flask import current_app
from flask.views import MethodView

from rados import Rados
from rados import Error as RadosError

from app.base import ApiResource

class CephClusterProperties(dict):
    """
    Validate ceph cluster connection properties
    """

    def __init__(self, config):
        dict.__init__(self)

        self['conffile'] = config['ceph_config']
        self['conf'] = dict()

        if 'keyring' in config:
            self['conf']['keyring'] = config['keyring']
        if 'client_id' in config and 'client_name' in config:
            raise RadosError("Can't supply both client_id and client_name")
        if 'client_id' in config:
            self['rados_id'] = config['client_id']
        if 'client_name' in config:
            self['name'] = config['client_name']


def getsnaplist(cluster, poolname):
    with cluster.open_ioctx(poolname) as ioctxobj:
        snaps = ioctxobj.list_snaps()
        return snaps


class SnapsResource(ApiResource):
    """
    Endpoint that shows overall cluster status
    """

    endpoint = 'snaps'
    url_prefix = '/snaps'
    url_rules = {
        'snaplist': {
            'rule': '/',
            'defaults': {'poolname': None},
        },
        'snaplist': {
            'rule': '/<string:poolname>'
        }
    }

    def __init__(self):
        MethodView.__init__(self)
        self.config = current_app.config['USER_CONFIG']
        self.clusterprop = CephClusterProperties(self.config)

    def get(self, poolname):
        if poolname is None:
            print '-------', url_for('poollist')
            return redirect(url_for('poollist'))
        else:
            with Rados(**self.clusterprop) as cluster:
                snaps = getsnaplist(cluster, str(poolname))
                return render_template('snaps.html', poolname=poolname, 
                                       snaps=snaps, config=self.config)
