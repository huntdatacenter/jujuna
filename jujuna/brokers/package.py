"""Package broker."""
from . import Broker, python3, load_output
from jujuna.exporters import Exporter
import logging


log = logging.getLogger('jujuna.tests.broker')


class Package(Broker):
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
                results = {'installed': []}
            # print(results['installed'].keys())
            if 'installed' in test_case:
                for condition in test_case['installed']:
                    rows.append((idx, '{} == {}'.format(condition, 'installed'), condition in results['installed']), )

        return rows
