"""File broker."""
from . import Broker, python3, load_output
from jujuna.exporters import Exporter
import logging


log = logging.getLogger('jujuna.tests.broker')


class File(Broker):
    """File broker."""

    def __init__(self):
        """Init broker."""
        super().__init__()

    async def run(self, test_data, unit, idx):
        """Run tests."""
        rows = []
        async with Exporter(unit, self.named) as exporter:
            files = test_data
            # print(test_data)

            for file, params in files.items():
                try:
                    act = await unit.run(python3(exporter, args=[file]), timeout=10)
                    results = load_output(act.data['results'])
                except Exception as exc:
                    log.debug(exc)
                    results = {}
                # print('Expect: ', files[file])
                # print(results)
                for param, value in params.items():
                    res = (param in results) and (results[param] == value)
                    rows.append((idx, '{}.{} == {}'.format(file, param, value), res), )

        return rows
