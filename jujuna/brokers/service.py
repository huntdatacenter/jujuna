"""Service broker."""
from . import Broker, python3, load_output
from jujuna.exporters import Exporter


class Service(Broker):
    """Service broker."""

    def __init__(self):
        """Init service broker."""
        super().__init__()

    async def run(self, test_case, unit, idx):
        """Run tests."""
        rows = []
        async with Exporter(unit, self.named) as exporter:
            act = await unit.run(python3(exporter), timeout=10)
            results = load_output(act.data['results'])
            # print(results['services'])
            # print(test_case)
            for service, condition in test_case.items():
                rows.append((idx, '{} == {}'.format(service, 'exists'), service in results['services']), )
                for c, v in condition.items():
                    rows.append((
                        idx, '{}.{} == {}'.format(service, c, v),
                        service in results['services'] and results['services'][service][c] == v
                    ), )

        return rows
