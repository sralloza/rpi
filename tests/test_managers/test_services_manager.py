import os

import pytest

from rpi.managers.services_manager import ServicesManager


class TestRaspberryService:
    def test_options_names_en(self):
        assert len(ServicesManager.AEMET.value.option_names_en) > 0
        assert len(ServicesManager.MENUS.value.option_names_en) > 0
        assert len(ServicesManager.VCS.value.option_names_en) > 0

    def test_option_names_en(self):
        assert len(ServicesManager.AEMET.value.option_names_es) > 0
        assert len(ServicesManager.MENUS.value.option_names_es) > 0
        assert len(ServicesManager.VCS.value.option_names_es) > 0

    def test_option_namespace(self):
        assert len(ServicesManager.AEMET.value.option_namespace) > 0
        assert len(ServicesManager.MENUS.value.option_namespace) > 0
        assert len(ServicesManager.VCS.value.option_namespace) > 0

    def test_filenames_with_ext(self):
        assert len(ServicesManager.AEMET.value.filenames_with_ext) > 0
        assert len(ServicesManager.MENUS.value.filenames_with_ext) > 0
        assert len(ServicesManager.VCS.value.filenames_with_ext) > 0
        assert len(ServicesManager.LOG.value.filenames_with_ext) > 0
        assert len(ServicesManager.TELEGRAM_BOT.value.filenames_with_ext) > 0
        assert len(ServicesManager.CONTROLLER.value.filenames_with_ext) > 0

    def test_filenames_without_ext(self):
        assert len(ServicesManager.AEMET.value.filenames_without_ext) > 0
        assert len(ServicesManager.MENUS.value.filenames_without_ext) > 0
        assert len(ServicesManager.VCS.value.filenames_without_ext) > 0
        assert len(ServicesManager.LOG.value.filenames_without_ext) > 0
        assert len(ServicesManager.TELEGRAM_BOT.value.filenames_without_ext) > 0
        assert len(ServicesManager.CONTROLLER.value.filenames_without_ext) > 0


class TestServicesManager:
    def test_get_menus(self):
        m1 = ServicesManager.get('menus_resi.py')
        m2 = ServicesManager.get('menus')
        m3 = ServicesManager.get('MENUS')

        assert m1 == ServicesManager.MENUS.value
        assert m2 == ServicesManager.MENUS.value
        assert m3 == ServicesManager.MENUS.value

    def test_get_aemet(self):
        a1 = ServicesManager.get('aemet.py')
        a2 = ServicesManager.get('aemet')
        a3 = ServicesManager.get('AEMET')
        assert a1 == ServicesManager.AEMET.value
        assert a2 == ServicesManager.AEMET.value
        assert a3 == ServicesManager.AEMET.value

    def test_get_vcs(self):
        v1 = ServicesManager.get('vcs.py')
        v2 = ServicesManager.get('vcs')
        v3 = ServicesManager.get('VCS')
        assert v1 == ServicesManager.VCS.value
        assert v2 == ServicesManager.VCS.value
        assert v3 == ServicesManager.VCS.value

    def test_get_telegram_bot(self):
        t1 = ServicesManager.get('telegram_bot.py')
        t2 = ServicesManager.get('telegram_bot')
        t3 = ServicesManager.get('TELEGRAM_BOT')
        assert t1 == ServicesManager.TELEGRAM_BOT.value
        assert t2 == ServicesManager.TELEGRAM_BOT.value
        assert t3 == ServicesManager.TELEGRAM_BOT.value

    def test_get_controller(self):
        c1 = ServicesManager.get('controller.py')
        c2 = ServicesManager.get('controller')
        c3 = ServicesManager.get('CONTROLLER')
        assert c1 == ServicesManager.CONTROLLER.value
        assert c2 == ServicesManager.CONTROLLER.value
        assert c3 == ServicesManager.CONTROLLER.value

    def test_get_log(self):
        l1 = ServicesManager.get('backup.py')
        l2 = ServicesManager.get('ngrok.py')
        l3 = ServicesManager.get('ngrok2.py')
        l4 = ServicesManager.get('reboot.py')
        l5 = ServicesManager.get('mails_manager.py')
        l6 = ServicesManager.get('sender.py')
        l7 = ServicesManager.get('pull.sh')
        l8 = ServicesManager.get('LOG')
        assert l1 == ServicesManager.LOG.value
        assert l2 == ServicesManager.LOG.value
        assert l3 == ServicesManager.LOG.value
        assert l4 == ServicesManager.LOG.value
        assert l5 == ServicesManager.LOG.value
        assert l6 == ServicesManager.LOG.value
        assert l7 == ServicesManager.LOG.value
        assert l8 == ServicesManager.LOG.value

    def test_eval(self):
        e1 = ServicesManager.eval('(MENUS, AEMET)')
        e2 = ServicesManager.eval('(AEMET, MENUS)')
        e3 = ServicesManager.eval('(LOG, TELEGRAM_BOT)')
        e4 = ServicesManager.eval('(TELEGRAM_BOT, LOG)')
        e5 = ServicesManager.eval('(CONTROLLER, VCS)')
        e6 = ServicesManager.eval('(VCS, CONTROLLER)')

        assert e1 == (ServicesManager.MENUS.value, ServicesManager.AEMET.value)
        assert e2 == (ServicesManager.AEMET.value, ServicesManager.MENUS.value)
        assert e3 == (ServicesManager.LOG.value, ServicesManager.TELEGRAM_BOT.value)
        assert e4 == (ServicesManager.TELEGRAM_BOT.value, ServicesManager.LOG.value)
        assert e5 == (ServicesManager.CONTROLLER.value, ServicesManager.VCS.value)
        assert e6 == (ServicesManager.VCS.value, ServicesManager.CONTROLLER.value)


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
