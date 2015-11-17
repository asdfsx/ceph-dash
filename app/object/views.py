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
from app.ceph_commands import rados


class ObjectsResource(ApiResource):
    """
    Endpoint that shows overall cluster status
    """

    endpoint = 'objects'
    url_prefix = '/objects'
    url_rules = {
        'objectempty': {
            'rule': '/',
            'defaults': {'poolname': None},
        },
        'objectlist':{
            'rule': '/<string:poolname>'
        }
    }

    def __init__(self):
        MethodView.__init__(self)
        self.config = current_app.config['USER_CONFIG']

    def get(self, poolname):
        if poolname is None:
            return redirect('/pools/')
        else:
            cmd = rados.rados()
            isSuccess, execresult = cmd.execute('ls', **{'pool':str(poolname),})
            print execresult
            if not isSuccess:
                abort(500, execresult)
            objects = json.loads(execresult)              
            print objects
            return render_template('objects.html', poolname=poolname, 
                                   objects=objects, config=self.config)
