#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json

from flask import request
from flask import render_template
from flask import abort
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


def list_pools(cluster):
    pools = cluster.list_pools()
    result = {}
    for pool in pools:
        result[pool] = getpoolstatus(cluster, pool)
    return result


def getpoolstatus(cluster, poolname):
    with cluster.open_ioctx(poolname) as ioctxobj:
        status = ioctxobj.get_stats()
        return status


class PoolResource(ApiResource):
    """
    Endpoint that shows overall cluster status
    """

    endpoint = 'pool'
    url_prefix = '/pool'
    url_rules = {
        'index': {
            'rule': '/',
        }
    }

    def __init__(self):
        MethodView.__init__(self)
        self.config = current_app.config['USER_CONFIG']
        self.clusterprop = CephClusterProperties(self.config)

    def get(self):
        with Rados(**self.clusterprop) as cluster:
            pools = list_pools(cluster)

            if request.mimetype == 'application/json':
                return jsonify(pools)
            else:
                return render_template('pool.html', pools=pools, config=self.config)

