"""User broker."""
from . import Broker, python3, load_output
from jujuna.exporters import Exporter
import logging


log = logging.getLogger('jujuna.tests.broker')


class User(Broker):
    """User broker."""

    def __init__(self):
        """Init User broker."""
        super().__init__()

    async def run(self, test_case, unit, idx):
        """Run tests."""
        rows = []
        async with Exporter(unit, self.named) as exporter:
            try:
                act = await unit.run(python3(exporter), timeout=10)
                user_data = load_output(act.data['results'])
            except Exception as exc:
                log.debug(exc)
                user_data = {}
            # print(user_data)
            for condition, test_item in test_case.items():
                test_res = False
                # if subitem in test_item.items():
                if condition in user_data and all(
                    user_data[condition][key] == value for key, value in test_item.items()
                ):
                    test_res = True
                rows.append((idx, '{} == {}'.format(condition, 'present'), test_res), )

        return rows
