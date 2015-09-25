# -*- coding: utf-8 -*-
"""
Core classes for communicating with the Bitbucket API.

Classes:
- Config: prototype for HTTP connection information
- Client: abstraction over HTTP requests to Bitbucket API
- BitbucketBase: parent class for Bitbucket resources
- BadRequestError: exception wrapping bad HTTP requests
- ServerError: exception wrapping server errors
"""
import json
from future.utils import python_2_unicode_compatible
from functools import partial
from requests import codes, Session
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from requests.utils import default_user_agent
from uritemplate import expand

from pybitbucket import metadata
from pybitbucket.entrypoints import entrypoints_json
from pybitbucket.util import links_from


class Config(object):
    bitbucket_url = 'api.bitbucket.org'
    username = 'pybitbucket'
    password = 'secret'
    email = 'pybitbucket@mailinator.com'


class Client(object):
    configurator = Config
    bitbucket_types = set()

    @staticmethod
    def user_agent_header():
        return u'%s/%s %s' % (
            metadata.package,
            metadata.version,
            default_user_agent())

    @staticmethod
    def start_http_session(auth, email=''):
        session = Session()
        session.auth = auth
        session.headers.update({
            'User-Agent': Client.user_agent_header(),
            'Accept': 'application/json',
            'From': email})
        return session

    @staticmethod
    def expect_ok(response, code=codes.ok):
        if code == response.status_code:
            return
        elif 400 == response.status_code:
            raise BadRequestError(response)
        elif 500 <= response.status_code:
            raise ServerError(response)
        else:
            response.raise_for_status()

    def convert_to_object(self, data):
        for t in Client.bitbucket_types:
            if t.is_type(data):
                return t(data, client=self)
        return data

    def remote_relationship(self, template, **keywords):
        url = expand(template, keywords)
        while url:
            response = self.session.get(url)
            self.expect_ok(response)
            json_data = response.json()
            if json_data.get('page'):
                for item in json_data.get('values'):
                    yield self.convert_to_object(item)
            else:
                yield self.convert_to_object(json_data)
            url = json_data.get('next')

    def get_bitbucket_url(self):
        return self.config.bitbucket_url

    def get_username(self):
        return self.config.username

    def __init__(self, config=None):
        if not config:
            config = self.configurator()
        self.config = config
        self.auth = HTTPBasicAuth(self.config.username, self.config.password)
        self.session = Client.start_http_session(self.auth, self.config.email)


@python_2_unicode_compatible
class BitbucketBase(object):
    id_attribute = 'id'

    def __init__(self, data, client=Client()):
        # Need some special handling for booleans.
        # Might be workaround for bug in the response JSON?
        data = {
            key: (
                (value in ('True', 'true'))
                if key.startswith('is_')
                else value)
            for (key, value)
            in data.items()}
        self.data = data
        self.client = client
        self.__dict__.update(data)
        for name, url in links_from(data):
            setattr(self, name, partial(
                self.client.remote_relationship,
                template=url))

    def delete(self):
        response = self.client.session.delete(self.links['self']['href'])
        # Deletes the snippet and returns 204 (No Content).
        Client.expect_ok(response, 204)
        return

    def put(self, data, **kwargs):
        response = self.client.session.put(
            self.links['self']['href'],
            data=data,
            **kwargs)
        Client.expect_ok(response)
        return self.client.convert_to_object(response.json())

    def attributes(self):
        return list(self.data.keys())

    def relationships(self):
        return list(self.data['links'].keys())

    def __repr__(self):
        return u'{name}({data})'.format(
            name=type(self).__name__,
            data=repr(self.data))

    def __str__(self):
        return u'{name} {id}:{data}'.format(
            name=type(self).__name__,
            id=self.id_attribute,
            data=getattr(self, self.id_attribute))


class Bitbucket(BitbucketBase):
    def __init__(self, client=Client()):
        self.client = client
        data = json.loads(entrypoints_json)
        for name, url in links_from(data):
            setattr(self, name, partial(
                self.client.remote_relationship,
                template=url))


class BadRequestError(HTTPError):
    def __init__(self, response):
        super(BadRequestError, self).__init__(u'''\
Attempted to request {url} but Bitbucket considered it a bad request.
{code} - {text}\
'''.format(
            url=response.url,
            code=response.status_code,
            text=response.text))


class ServerError(HTTPError):
    def __init__(self, response):
        super(ServerError, self).__init__(u'''\
Attempted to request {url} but encountered a server error.
{code} - {text}\
'''.format(
            url=response.url,
            code=response.status_code,
            text=response.text))
