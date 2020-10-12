"""Mount broker."""
from . import Broker, python3, load_output
from jujuna.exporters import Exporter
import re
import logging


log = logging.getLogger('jujuna.tests.broker')


class Mount(Broker):
    """Mount broker."""

    def __init__(self):
        """Init broker."""
        super().__init__()

    async def run(self, test_case, unit, idx):
        """Run tests."""
        rows = []
        async with Exporter(unit, self.named) as exporter:
            try:
                act = await unit.run(python3(exporter), timeout=10)
                results = load_output(act.data['results'])
            except Exception as exc:
                log.debug(exc)
                results = []
            # print(results.keys())
            if 'regex' in test_case:
                for condition in test_case['regex']:
                    prog = re.compile(condition)
                    mounts = ''

                    for result in results:
                        var = prog.search(result)
                        if var:
                            mounts = var.group(0)

                    rows.append((idx, '{} == {}'.format(
                        mounts if mounts else str(condition), 'mounted'
                    ), True if mounts else False), )

        return rows
