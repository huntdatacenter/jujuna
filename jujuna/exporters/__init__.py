"""Exporter management."""

import os
import uuid
import logging
import async_timeout


log = logging.getLogger('jujuna.tests.exporter')


class Exporter():
    """Exporter context manager."""

    def __init__(self, unit, exporter_name, timeout=15):
        """Init exporter."""
        if exporter_name.endswith('.py'):
            raise Exception('Do not provide an extension')
        self.timeout = timeout
        self.unit = unit
        self.full_path = os.path.dirname(os.path.realpath(__file__))
        self.exporter_local = os.path.join(self.full_path, exporter_name + '.py')
        if not os.path.isfile(self.exporter_local):
            raise Exception('Exporter: {}.py not found'.format(exporter_name))
        self.exporter_remote = os.path.join('/tmp', str(uuid.uuid4())[:9] + exporter_name + '.py')

    async def __aenter__(self):
        """Upload exporter and return remote path."""
        # print('Load: ', self.exporter_local)
        await self._load_exporter(self.unit, self.exporter_local, self.exporter_remote)
        return self.exporter_remote

    async def __aexit__(self, type, value, traceback):
        """Dispose remote exporter."""
        # print('Unload: ', self.exporter_remote)
        await self._unload_exporter(self.unit, self.exporter_remote)

    async def _load_exporter(self, unit, source, target, user='ubuntu'):
        """Upload exporter."""
        for i in range(3):
            try:
                async with async_timeout.timeout(self.timeout):
                    await unit.scp_to(
                        source,
                        target,
                        user=user
                    )
                break
            except Exception as exc:
                log.debug(exc)

    async def _unload_exporter(self, unit, target, user='ubuntu'):
        """Dispose of remote exporter."""
        ret = None
        for i in range(3):
            try:
                async with async_timeout.timeout(self.timeout):
                    ret = await unit.run('rm {}'.format(target), timeout=self.timeout - 1)
                break
            except Exception as exc:
                # Try 3 times, if it fails raise on last
                if i == 2 and 'No such file' not in str(exc):
                    log.warning('Unload failed: {}'.format(str(exc)))
                    log.debug(exc)
        # ret = await unit.run('rm /tmp/*.py', timeout=3)
        if (
            ret and ret.data and
            'results' in ret.data and
            ret.data['results']['Code'] != '0' and
            'No such file' not in ret.data['results']['Stderr']
        ):
            log.warn('Unload failed: {}'.format(ret.data['results']['Stderr']))
