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
from rbd import RBD
from rbd import Image 

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


def getsnaplist(cluster, poolname, imagename):
    with cluster.open_ioctx(poolname) as ioctxobj:
        image = Image(ioctxobj, imagename)
        snaps = image.list_snaps()
        return snaps


class SnapsResource(ApiResource):
    """
    Endpoint that shows overall cluster status
    """

    endpoint = 'snaps'
    url_prefix = '/snaps'
    url_rules = {
        'snaplist':{
            'rule': '/<string:poolname>/<string:imagename>',
            'method':['GET','POST','DELETE'],
        }
    }

    def __init__(self):
        MethodView.__init__(self)
        self.config = current_app.config['USER_CONFIG']
        self.clusterprop = CephClusterProperties(self.config)

    def get(self, poolname, imagename):
        if poolname is None:
            return redirect("/pools/")
        elif imagename is None:
            return redirect("/images/"+poolname)
        else:
            with Rados(**self.clusterprop) as cluster:
                snaps = getsnaplist(cluster, str(poolname), str(imagename))
                return render_template('snaps.html', poolname=poolname, imagename=imagename,
                                       snaps=snaps, config=self.config)
