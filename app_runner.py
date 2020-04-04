import os
import multiprocessing
from pprint import pprint
import random
from gunicorn.six import iteritems
from gunicorn.app.base import BaseApplication
from werkzeug.wsgi import DispatcherMiddleware
from prometheus_client import make_wsgi_app, Counter, Histogram, Summary, Gauge

G_WORKER_NUM = os.getenv("GUNICORN_WORKER_NUM",
                         multiprocessing.cpu_count() + 1)


class StandaloneApplication(BaseApplication):
    def init(self, parser, opts, args):
        pass

    def __init__(self, app, option=None, *args, **kwargs):
        self.options = option or {}
        self.application = app
        super(StandaloneApplication, self).__init__(*args, **kwargs)

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def run_gunicorn():
    from app import create_app
    app = create_app()
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {'/metrics': make_wsgi_app()})
    pprint(app.url_map)
    options = {
        'bind': '0.0.0.0:2333',
        'workers': G_WORKER_NUM,
        # gevent worker will cause captain can't create unix daemon
        # 'worker_class': 'gevent',
        'accesslog': '-',
        'errorlog': '-',
        'timeout': 300,
    }
    StandaloneApplication(app, options).run()


gg = Gauge("gg", "a gauge")
gg.set(random.random())


if __name__ == '__main__':
    # apply patch before import requests etc
    # gevent.monkey.patch_all()
    # initialization or migration db
    from manage import initdb
    from models.templates.settings import init_system_info, init_registry_address

    #
    initdb()
    init_system_info()
    init_registry_address()
    run_gunicorn()

