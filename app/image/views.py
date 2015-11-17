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

from app.base import ApiResource
from app.ceph_commands import rbd


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

    def get(self, poolname):
        if poolname is None:
            return redirect('/pools/')
        else:
            cmd = rbd.rbd()
            isSuccess, execresult = cmd.execute('ls', **{'pool':str(poolname)})
            if not isSuccess:
                abort(500, execresult)
            images = json.loads(execresult)
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

    def get(self, poolname, imagename):
        if poolname is None:
            return redirect('/pools/')
        elif imagename is None:
            return redirect('/images/'+poolname)
        else:
            cmd = rbd.rbd()
            isSuccess, execresult = cmd.execute('info', **{'pool':str(poolname),'image':str(imagename)})
            if not isSuccess:
                abort(500, execresult)
            image_info = json.loads(execresult)
            stat = image_info
            stat['size'] = "%s MB" % (image_info['size']/1024/1024,)
            stat['obj_size'] = "%s KB" % (image_info['object_size']/1024, )
            return render_template('image.html', 
                                   poolname=poolname, imagename=imagename,
                                   imagestatus=stat, config=self.config)
