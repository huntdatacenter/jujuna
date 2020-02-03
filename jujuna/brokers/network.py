"""Network broker."""
from . import Broker, python3, load_output
from jujuna.exporters import Exporter
import logging


log = logging.getLogger('jujuna.tests.broker')


class Network(Broker):
    """Network broker."""

    def __init__(self):
        """Init broker."""
        super().__init__()

    async def run(self, test_case, unit, idx):
        """Run tests."""
        rows = []
        async with Exporter(unit, self.named) as exporter:
            if 'port' in test_case:
                try:
                    test_data = await unit.run(python3(exporter), timeout=10)
                    results = load_output(test_data.data['results'])
                except Exception as exc:
                    log.debug(exc)
                    results = {'sockets': []}
                # print(results)

                local_ports = [str(s['local_port']) for s in results['sockets']]

                for port, open in test_case['port'].items():
                    status = 'open' if open else 'closed'
                    rows.append((idx, '{}.{} == {}'.format('port', port, status), (str(port) in local_ports) == open), )

        return rows
