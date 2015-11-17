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
from app.ceph_commands import ceph

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


class CephClusterCommand(dict):
    """
    Issue a ceph command on the given cluster and provide the returned json
    """

    def __init__(self, cluster, **kwargs):
        dict.__init__(self)
        ret, buf, err = cluster.mon_command(json.dumps(kwargs), '', timeout=5)
        if ret != 0:
            self['err'] = err
        else:
            self.update(json.loads(buf))


def list_pools(cluster):
    pools = cluster.list_pools()
    return pools


def getpoolstatus(cluster, poolname):
    with cluster.open_ioctx(poolname) as ioctxobj:
        status = ioctxobj.get_stats()
        return status

def getpoolparameter(cluster, poolname):
    dump = CephClusterCommand(cluster, prefix="osd dump", format='json')
    if "err" not in dump:
        for pool in dump['pools']:
            if pool['pool_name'] == poolname:
                return pool
    return {}

def createpool(cluster, poolname):
    cluster.create_pool(poolname)


def deletepool(cluster, poolname):
    cluster.delete_pool(poolname)


##################
#     ceph df result
#   {u'pools': [{u'stats': {u'bytes_used': 196460930, u'max_avail': 169573305206, u'objects': 2734, u'kb_used': 191857}, u'name': u'rbd', u'id': 4}, {u'stats': {u'bytes_used': 72614311, u'max_avail': 169573305206, u'objects': 92, u'kb_used': 70913}, u'name': u'mypool', u'id': 5}, {u'stats': {u'bytes_used': 0, u'max_avail': 169573305206, u'objects': 0, u'kb_used': 0}, u'name': u'flask_test', u'id': 13}], 
#    u'stats': {u'total_used_bytes': 930623488, u'total_bytes': 509773004800, u'total_avail_bytes': 508842381312}}
##################

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
            cmd = ceph.ceph()
            isSuccess, execresult = cmd.execute('df')
            if not isSuccess:
                abort(500, execresult)
            pool_status = json.loads(execresult)
            stats = {}
            stats['total_used_bytes'] = pool_status['stats']['total_used_bytes']
            stats['total_bytes'] = pool_status['stats']['total_bytes']
            stats['total_avail_bytes'] = pool_status['stats']['total_avail_bytes']

            pools = []
            for pool in pool_status['pools']:
                tmp = {'id': pool['id'], 'name': pool['name'],
                       'objects': pool['stats']['objects'], 
                       'bytes_used': pool['stats']['bytes_used'],
                       'kb_used': pool['stats']['kb_used'], 
                       'max_avail': pool['stats']['max_avail'],}
                pools.append(tmp)
            return render_template('pools.html', stats=stats, pools=pools, config=self.config)
        else:
            with Rados(**self.clusterprop) as cluster:
                cmd = ceph.ceph()
                isSuccess, execresult = cmd.execute('osddump')
                if not isSuccess:
                    abort(500, execresult)
                osddump = json.loads(execresult)
                parameters = {}
                if 'pools' in osddump:
                    for pool in osddump['pools']:
                        if pool['pool_name'] == poolname:
                            parameters = pool
                poolstatus = getpoolstatus(cluster, str(poolname))
                return render_template('pool.html', poolname=poolname, poolstatus=poolstatus,
                                       parameters=parameters, config=self.config)

    def post(self):
        poolname = request.form['poolname']
        if poolname is None:
            return jsonify(status="fail")
        else:
            with Rados(**self.clusterprop) as cluster:
                createpool(cluster, str(poolname))
                return jsonify(status="success")

    def delete(self, poolname):
        if poolname is None:
            return jsonify(status="fail")
        else:
            with Rados(**self.clusterprop) as cluster:
                deletepool(cluster, str(poolname))
                return jsonify(status="success")
