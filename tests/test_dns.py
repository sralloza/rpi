import os

import pytest

from rpi.dns import RpiDns
from rpi.exceptions import DnsError, PlatformError


class TestDns:
    def test_dns_add_one(self):
        assert RpiDns.len() >= 0

        RpiDns.new_alias('text.test_one', 'D:/test/dns')

        with pytest.raises(DnsError, match='already exists'):
            RpiDns.new_alias('text.test_one', 'D:/test/dns')

        with pytest.raises(DnsError, match='Not enough subalias'):
            RpiDns.new_alias('', 'D:/test/dns/not-enough-subalias')

        with pytest.raises(PlatformError, match='Invalid platform'):
            RpiDns.new_alias('rpi.text.test_one_independendant', 'D:/')

    def test_dns_add_multiple(self):
        with pytest.raises(DnsError, match='For dual alias, 2 subalias must be given'):
            RpiDns.new_dual_alias('only-one-alias', 'D:/test/dns/dual',
                                  '/home/test/dns/dual')

        RpiDns.new_dual_alias('text.test-multiple', 'D:/test/dns/dual-success',
                              '/home/test/dns/dual-success')

    def test_dns_delete(self):
        with pytest.raises(DnsError, match='linux'):
            RpiDns.del_alias('text.test_one', error=False)

        RpiDns.del_alias('text.test-multiple')


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
