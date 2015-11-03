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

###################
#
#ceph osd df result
#    {u'nodes': [{u'kb': 99565040, u'name': u'osd.0', u'type_id': 0, u'reweight': 1.0, u'crush_weight': 0.089996, u'utilization': 0.169312, 
#                 u'depth': 2, u'kb_avail': 99396464, u'kb_used': 168576, u'var': 0.927465, u'type': u'osd', u'id': 0}, 
#                 {u'kb': 99565040, u'name': u'osd.1', u'type_id': 0, u'reweight': 1.0, u'crush_weight': 0.089996, u'utilization': 0.206579, 
#                  u'depth': 2, u'kb_avail': 99359360, u'kb_used': 205680, u'var': 1.131602, u'type': u'osd', u'id': 1}, 
#                 {u'kb': 99565040, u'name': u'osd.2', u'type_id': 0, u'reweight': 1.0, u'crush_weight': 0.089996, u'utilization': 0.204144, 
#                  u'depth': 2, u'kb_avail': 99361784, u'kb_used': 203256, u'var': 1.118266, u'type': u'osd', u'id': 2}, 
#                 {u'kb': 99565040, u'name': u'osd.3', u'type_id': 0, u'reweight': 1.0, u'crush_weight': 0.089996, u'utilization': 0.1821, 
#                  u'depth': 2, u'kb_avail': 99383732, u'kb_used': 181308, u'var': 0.997513, u'type': u'osd', u'id': 3}, 
#                 {u'kb': 99565040, u'name': u'osd.5', u'type_id': 0, u'reweight': 1.0, u'crush_weight': 0.089996, u'utilization': 0.150635, 
#                  u'depth': 2, u'kb_avail': 99415060, u'kb_used': 149980, u'var': 0.825154, u'type': u'osd', u'id': 5}], 
#     u'stray': [], 
#     u'summary': {u'total_kb': 497825200, u'dev': 0.021155, u'max_var': 1.131602, u'total_kb_avail': 496916400, u'min_var': 0.825154, 
#                  u'average_utilization': 0.182554, u'total_kb_used': 908800}
#    }
#
#
#ceph osd perf result
#    {u'osd_perf_infos': 
#     [{u'id': 0, u'perf_stats': {u'apply_latency_ms': 64, u'commit_latency_ms': 34}}, 
#      {u'id': 1, u'perf_stats': {u'apply_latency_ms': 53, u'commit_latency_ms': 30}}, 
#      {u'id': 2, u'perf_stats': {u'apply_latency_ms': 7, u'commit_latency_ms': 4}}, 
#      {u'id': 3, u'perf_stats': {u'apply_latency_ms': 21, u'commit_latency_ms': 11}}, 
#      {u'id': 5, u'perf_stats': {u'apply_latency_ms': 255, u'commit_latency_ms': 75}}]}
#
#
#ceph osd maxosd result
#    {u'epoch': 190, u'max_osd': 6}
#
#
###################


class DisksResource(ApiResource):
    """
    Endpoint that shows overall cluster status
    """

    endpoint = 'disks'
    url_prefix = '/disks'
    url_rules = {
        'disklist': {
            'rule': '/',
        }
    }

    def __init__(self):
        MethodView.__init__(self)
        self.config = current_app.config['USER_CONFIG']
        self.clusterprop = CephClusterProperties(self.config)

    def get(self):
        with Rados(**self.clusterprop) as cluster:
            disk_status = CephClusterCommand(cluster, prefix='osd df', format='json')
            if 'err' in disk_status:
                abort(500, disk_status['err'])
            summary = disk_status['summary']
 
            disk_perf = CephClusterCommand(cluster, prefix='osd perf', format='json')
            if 'err' in disk_perf:
                abort(500, disk_perf['err'])

            disk_maxosd = CephClusterCommand(cluster, prefix='osd getmaxosd', format='json')
            if 'err' in disk_maxosd:
                abort(500, disk_maxosd['err'])
            summary['max_osd'] = disk_maxosd['max_osd']
            summary['epoch'] = disk_maxosd['epoch']

            nodes = {}
            title = ['name','var','crush_weight','utilization','kb_used','kb_avail','kb',]
            for node in disk_status['nodes']:
                tmp = {}
                for t in title:
                    tmp[t] = node[t]
                nodes[node['id']] = tmp
            
            title.append('apply_latency_ms')
            title.append('commit_latency_ms')
            for perf in disk_perf['osd_perf_infos']:
                if perf['id'] in nodes:
                    nodes[perf['id']]['apply_latency_ms'] = perf['perf_stats']['apply_latency_ms']
                    nodes[perf['id']]['commit_latency_ms'] = perf['perf_stats']['commit_latency_ms']

            return render_template('disks.html', summary=summary, nodes=nodes, title=title, config=self.config)

