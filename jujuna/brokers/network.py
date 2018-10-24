"""Network broker."""
from . import Broker, python3, load_output
from jujuna.exporters import Exporter


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
                test_data = await unit.run(python3(exporter), timeout=10)
                results = load_output(test_data.data['results'])
                # print(results)

                local_ports = [s['local_port'] for s in results['sockets']]

                for port in test_case['port']:
                    rows.append((idx, '{}.{} == {}'.format('port', port, 'open'), port in local_ports), )

        return rows
