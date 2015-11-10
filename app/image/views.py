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


def getimagelist(cluster, poolname):
    with cluster.open_ioctx(poolname) as ioctxobj:
        rbd_inst = RBD()
        return rbd_inst.list(ioctxobj)


def getimagestat(cluster,poolname, imagename):
    with cluster.open_ioctx(poolname) as ioctxobj:
        image = Image(ioctxobj, imagename)
        stat = image.stat()
        old_format = image.old_format()
        feature = image.features()
        stat['old_format'] = old_format
        stat['feature'] = feature
        stat['size'] = "%s MB" % (stat['size']/1024/1024,)
        stat['obj_size'] = "%s KB" % (stat['obj_size']/1024, )
        return stat


class ImagesResource(ApiResource):
    """
    Endpoint that shows overall cluster status
    """

    endpoint = 'images'
    url_prefix = '/images'
    url_rules = {
        'imagesoperate': {
            'rule': '/',
            'defaults': {'poolname': None},
        },
        'imagesoperate':{
            'rule': '/<string:poolname>',
            'method':['GET','POST','DELETE'],
        }
    }

    def __init__(self):
        MethodView.__init__(self)
        self.config = current_app.config['USER_CONFIG']
        self.clusterprop = CephClusterProperties(self.config)

    def get(self, poolname):
        if poolname is None:
            return redirect('/pools/')
        else:
            with Rados(**self.clusterprop) as cluster:
                images = getimagelist(cluster, str(poolname))
                return render_template('images.html', poolname=poolname, 
                                       images=images, config=self.config)


class ImageResource(ApiResource):
    """
    Endpoint that shows overall cluster status
    """

    endpoint = 'image'
    url_prefix = '/image'
    url_rules = {
        'imageoperate': {
            'rule': '/',
            'defaults': {'imagename': None},
        },
        'imageoperate':{
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
            return redirect('/pools/')
        elif imagename is None:
            return redirect('/images/'+poolname)
        else:
            with Rados(**self.clusterprop) as cluster:
                stat = getimagestat(cluster, str(poolname), str(imagename))
                return render_template('image.html', 
                                       poolname=poolname, imagename=imagename,
                                       imagestatus=stat, config=self.config)
