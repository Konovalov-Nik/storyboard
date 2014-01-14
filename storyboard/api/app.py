# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from oslo.config import cfg
import pecan
from storyboard.openstack.common.gettextutils import _  # noqa
from storyboard.openstack.common import log
from wsgiref import simple_server

from storyboard.api import config as api_config

CONF = cfg.CONF
LOG = log.getLogger(__name__)

API_OPTS = [
    cfg.StrOpt('host',
               default='0.0.0.0',
               help='API host'),
    cfg.IntOpt('port',
               default=8080,
               help='API port')
]
CONF.register_opts(API_OPTS, 'api')


def get_pecan_config():
    # Set up the pecan configuration
    filename = api_config.__file__.replace('.pyc', '.py')
    return pecan.configuration.conf_from_file(filename)


def setup_app(pecan_config=None):
    if not pecan_config:
        pecan_config = get_pecan_config()

    app = pecan.make_app(
        pecan_config.app.root,
        debug=CONF.debug,
        force_canonical=getattr(pecan_config.app, 'force_canonical', True),
        guess_content_type_from_ext=False
    )

    cfg.set_defaults(log.log_opts,
                     default_log_levels=[
                         'storyboard=INFO',
                         'sqlalchemy=WARN'
                     ])
    log.setup('storyboard')

    return app


def start(argv=None):
    CONF(argv, project='storyboard')
    root = setup_app()

    # Create the WSGI server and start it
    host = cfg.CONF.api.host
    port = cfg.CONF.api.port
    srv = simple_server.make_server(host, port, root)

    LOG.info(_('Starting server in PID %s') % os.getpid())
    LOG.info(_("Configuration:"))
    if host == '0.0.0.0':
        LOG.info(_(
            'serving on 0.0.0.0:%(sport)s, view at http://127.0.0.1:%(vport)s')
            % ({'sport': port, 'vport': port}))
    else:
        LOG.info(_("serving on http://%(host)s:%(port)s") % (
                 {'host': host, 'port': port}))

    srv.serve_forever()
