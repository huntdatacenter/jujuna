"""File broker."""
from . import Broker, python3, load_output
from jujuna.exporters import Exporter


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
                act = await unit.run(python3(exporter, args=[file]), timeout=10)
                results = load_output(act.data['results'])
                # print('Expect: ', files[file])
                # print(results)
                for param, value in params.items():
                    res = results[param] == value
                    rows.append((idx, '{}.{} == {}'.format(file, param, value), res), )

        return rows
