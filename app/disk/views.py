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


def find_host_for_osd(osd, osd_status):
    """ find host for a given osd """

    for obj in osd_status['nodes']:
        if obj['type'] == 'host':
            if osd in obj['children']:
                return obj['name']

    return 'unknown'


def get_unhealthy_osd_details(osd_status):
    """ get all unhealthy osds from osd status """

    unhealthy_osds = list()

    for obj in osd_status['nodes']:
        if obj['type'] == 'osd':
            # if OSD does not exists (DNE in osd tree) skip this entry
            if obj['exists'] == 0:
                continue
            if obj['status'] == 'down' or obj['status'] == 'out':
                # It is possible to have one host in more than one branch in the tree.
                # Add each unhealthy OSD only once in the list
                entry = {
                    'name': obj['name'],
                    'status': obj['status'],
                    'host': find_host_for_osd(obj['id'], osd_status)
                }
                if entry not in unhealthy_osds:
                    unhealthy_osds.append(entry)

    return unhealthy_osds


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
 
            headline = []
            nodes = []
            for key in disk_status['nodes'][0]:
                headline.append(key)
            nodes.append(headline)
            for node in disk_status['nodes']:
                tmp = []
                for k in headline:
                    tmp.append(node[k])
                nodes.append(tmp)
            return render_template('disks.html', summary=summary, nodes=nodes, config=self.config)

