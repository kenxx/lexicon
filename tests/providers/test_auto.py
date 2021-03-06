# Test for one implementation of the interface
import socket
from unittest import TestCase

import mock
import pytest

from lexicon.providers.auto import Provider
from lexicon.providers.auto import _get_ns_records_domains_for_domain
from integration_tests import IntegrationTests

# This fixture ensures to mock _get_ns_records_domains_for_domain, in order to not rely 
# on the machine on which the test is done, as this function call nslookup.
# Then it will prevent errors where there is no network or tested domain do not exists anymore.
@pytest.fixture(autouse=True)
def nslookup_mock(request):
    _ignore_nslookup_mock = request.node.get_marker('ignore_nslookup_mock')

    if (_ignore_nslookup_mock):
        # Do not mock if the test says so.
        yield
    else:
        with mock.patch('lexicon.providers.auto._get_ns_records_for_domain',
                        return_value=['ns.ovh.net']) as fixture:
            yield fixture

# Guys, are we online ?
def there_is_no_network():
    try:
        socket.create_connection(("www.google.com", 80))
        return False
    except OSError:
        pass
    return True

# Hook into testing framework by inheriting unittest.TestCase and reuse
# the tests which *each and every* implementation of the interface must
# pass, by inheritance from integration_tests.IntegrationTests
class OvhProviderTests(TestCase, IntegrationTests):

    Provider = Provider
    provider_name = 'auto'
    domain = 'pacalis.net'

    def _filter_headers(self):
        return ['X-Ovh-Application', 'X-Ovh-Consumer', 'X-Ovh-Signature']

    # Override _test_options to call env_auth_options and then import auth config from env variables
    def _test_options(self):
        cmd_options = super(OvhProviderTests, self)._test_options()
        cmd_options.update({'auth_entrypoint':'ovh-eu'})
        return cmd_options

    # Here we do not mock the function _get_ns_records_domains_for_domain
    # to effectively test the nslookup call and processing.\
    @pytest.mark.skipif(there_is_no_network(), reason='No network, no nslookup call possible.')
    @pytest.mark.ignore_nslookup_mock('yes')
    def test_nslookup_resolution(self):
        """Ensure that nameservers can be resolved through os nslookup call."""
        assert _get_ns_records_domains_for_domain('google.com')
