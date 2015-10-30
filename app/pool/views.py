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
    return pools


def getpoolstatus(cluster, poolname):
    with cluster.open_ioctx(poolname) as ioctxobj:
        status = ioctxobj.get_stats()
        print status
        return status

def createpool(cluster, poolname):
    cluster.create_pool(poolname)

class PoolsResource(ApiResource):
    """
    Endpoint that shows overall cluster status
    """

    endpoint = 'pools'
    url_prefix = '/pools'
    url_rules = {
        'pool_list': {
            'rule': '/',
            'method':['GET'],
            'defaults': {'poolname': None},
        },
        'pool_create':{
            'rule': '/',
            'method':['POST'],
        },
        'pool_operate':{
            'rule': '/<poolname>',
            'method':['GET', 'PUT', 'DELETE']
        }
    }

    def __init__(self):
        MethodView.__init__(self)
        self.config = current_app.config['USER_CONFIG']
        self.clusterprop = CephClusterProperties(self.config)

    def get(self, poolname):
        if poolname is None:
            with Rados(**self.clusterprop) as cluster:
                pools = list_pools(cluster)
                return render_template('pools.html', pools=pools, config=self.config)
        else:
            with Rados(**self.clusterprop) as cluster:
                poolstatus = getpoolstatus(cluster, str(poolname))
                return render_template('pool.html', poolname=poolname, 
                                       poolstatus=poolstatus, config=self.config)

    def post(self):
        poolname = request.form['poolname']
        if poolname is None:
            return jsonify(status="fail")
        else:
            with Rados(**self.clusterprop) as cluster:
                createpool(cluster, str(poolname))
                return jsonify(status="success")
