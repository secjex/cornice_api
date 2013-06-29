"""Main entry point
"""
from couchdb.client import Server
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.events import subscriber, NewRequest, BeforeRender
from pyramid.security import authenticated_userid, Allow


@subscriber(NewRequest)
def add_couchdb_to_request(event):
    request = event.request
    settings = request.registry.settings
    db = settings['CouchDB.server'][settings['CouchDB.db_name']]
    event.request.db = db


@subscriber(BeforeRender)
def context_processor(event):
    event.rendering_val['user_login'] = authenticated_userid(event['request'])


class RootFactory(object):
    __acl__ = [
        (Allow, 'admin', 'view'),
        (Allow, 'admin', 'edit')]

    def __init__(self, request):
        pass


def main(global_config, **settings):
    auth_token = AuthTktAuthenticationPolicy('what_makes_so_secret', hashalg='sha512')
    auth_permission = ACLAuthorizationPolicy()
    config = Configurator(settings=settings,
                          root_factory=RootFactory)
    config.set_authentication_policy(auth_token)
    config.set_authorization_policy(auth_permission)
    db_server = Server(url=settings['CouchDB.url'])
    if settings['CouchDB.db_name'] not in db_server:
        db_server.create(settings['CouchDB.db_name'])
    config.registry.settings['CouchDB.server'] = db_server
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.include("cornice")
    config.scan("api.views")
    return config.make_wsgi_app()