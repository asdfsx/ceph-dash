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
from app.ceph_commands import ceph


class MDSResource(ApiResource):
    """
    Endpoint that shows overall cluster status
    """

    endpoint = 'mds'
    url_prefix = '/mds'
    url_rules = {
        'mds': {
            'rule': '/',
        },
    }

    def __init__(self):
        MethodView.__init__(self)
        self.config = current_app.config['USER_CONFIG']

    def get(self):
        cmd = ceph.ceph()
        isSuccess, execresult = cmd.execute('mdstat')
        if not isSuccess:
            abort(500, execresult)
        mdstat = json.loads(execresult)              
        return render_template('mds.html', 
                               mdstat=mdstat, config=self.config)
