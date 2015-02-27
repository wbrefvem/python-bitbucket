import types
from uritemplate import expand

from pybitbucket.bitbucket import Config
from pybitbucket.bitbucket import Client


class Snippet(object):
    @staticmethod
    def url(username, id):
        template = 'https://{+bitbucket_url}/2.0/snippets/{username}/{id}'
        return expand(template, {'bitbucket_url': Config.bitbucket_url(),
                                 'username': username,
                                 'id': id})

    def __init__(self, client, d):
        self.client = client
        self.__dict__.update(d)
        for link, href in d['links'].iteritems():
            for head, url in href.iteritems():
                # watchers, comments, and commits
                setattr(self, link, types.MethodType(
                    self.client.paginated_get, url))

    def __str__(self):
        return '\n'.join("id          : {}".format(self.id),
                         "is_private  : {}".format(self.is_private),
                         "is_unlisted : {}".format(self.is_unlisted),
                         "title       : {}".format(self.title),
                         "files       : {}".format(self.files),
                         "creator     : {}".format(self.creator),
                         "created_on  : {}".format(self.created_on),
                         "owner       : {}".format(self.owner),
                         "updated_on  : {}".format(self.updated_on),
                         "scm         : {}".format(self.scm),
                         )

    # PUT one
    # {"title": "Updated title"}
    def rename(self, title):
        pass

    # PUT one
    def add(self, files):
        pass

    # DELETE one
    def delete(self):
        url = Snippet.url(self.client.username, self.id)
        r = self.client.session.delete(url)
        # Deletes the snippet and returns 204 (No Content).
        if 204 == r.status_code:
            return
        else:
            raise Exception

    # GET files
    def content(self):
        pass

    # GET one
    def commit(self, sha1):
        pass


class Role(object):
    OWNER = 'owner'
    CONTRIBUTOR = 'contributor'
    MEMBER = 'member'
    roles = [OWNER, CONTRIBUTOR, MEMBER]


def create_snippet(files,
                   client=Client(),
                   is_private=False,
                   is_unlisted=False,
                   title='',
                   scm='git'):
    template = 'https://{+bitbucket_url}/2.0/snippets/{username}'
    url = expand(template, {'bitbucket_url': Config.bitbucket_url(),
                            'username': client.config.username})
    payload = {
        'title': title,
        #'is_private': is_private,
        #'is_unlisted': is_unlisted,
        #'scm': scm,
        }
    response = client.session.post(url, data=payload, files=files)
    return Snippet(client, response.json())


def find_snippets_for_role(client, role=Role.OWNER):
    if role not in Role.roles:
        raise NameError("role '%s' is not in [%s]" %
                        (role, '|'.join(str(x) for x in Role.roles)))
    template = 'https://{+bitbucket_url}/2.0/snippets{?role}'
    url = expand(template, {'bitbucket_url': Config.bitbucket_url(),
                            'role': role})
    for snip in client.paginated_get(url):
        yield Snippet(client, snip)


def find_snippet_by_id(client, id):
    url = Snippet.url(client.config.username, id)
    response = client.session.get(url)
    if 200 == response.status_code:
        return Snippet(client, response.json())