# -*- coding: utf-8 -*-
from os import path
from test_auth import TestAuth
from pybitbucket.bitbucket import Client

import json
from pybitbucket.bitbucket import BitbucketBase


class BitbucketFixture(object):
    # GIVEN: a class under test
    class_under_test = 'Bitbucket'

    # GIVEN: a utility for deciding where test data lives
    @classmethod
    def test_dir(cls):
        this_dir, this_file = path.split(path.abspath(__file__))
        return this_dir

    # GIVEN: a utility for loading json files
    @classmethod
    def data_from_file(cls, filename, directory=None):
        if (directory is None):
            directory = cls.test_dir()
        filepath = path.join(directory, filename)
        with open(filepath) as f:
            data = f.read()
        return data

    # GIVEN: A test Bitbucket client with test credentials
    test_client = Client(TestAuth())

    # GIVEN: Example data for a resource
    @classmethod
    def resource_data(cls):
        file_name = '{}.json'.format(cls.class_under_test)
        return cls.data_from_file(file_name)

    # GIVEN: Example data for a set of resources
    @classmethod
    def resource_list_data(cls):
        file_name = '{}_list.json'.format(cls.class_under_test)
        return cls.data_from_file(file_name)

    # GIVEN: The URL for the example resource
    @classmethod
    def resource_url(cls):
        o = cls.example_object()
        return o.links['self']['href']


class BitbucketBaseFixture(BitbucketFixture):
    # GIVEN: Example data for a Bitbucket resource with links
    @classmethod
    def repository_data(cls):
        return cls.data_from_file('example_single_repository.json')


class TestGettingLinksFromExampleData(BitbucketBaseFixture):
    @classmethod
    def setup_class(cls):
        data = json.loads(cls.repository_data())
        cls.links = {
            name: url
            for (name, url)
            in BitbucketBase.links_from(data)}

    def test_includes_a_link_named_self(self):
        # Much of the v2 classification relies on parsing self.
        assert self.links.get('self')

    def test_does_not_include_the_quirky_clone_link(self):
        # Clone links do not follow HAL conventions.
        # And they cannot be traversed with an HTTP client.
        assert not self.links.get('clone')

    def test_count_matches_seven(self):
        # Count of the links in the example data,
        # not including the clone links.
        assert 7 == len(list(self.links))
