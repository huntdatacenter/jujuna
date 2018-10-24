"""Broker abstract class."""
import json


class Broker():
    """Broker abstract class."""

    def __init__(self):
        """Init abstract class."""
        self.named = self.__class__.__name__.lower()

    async def run(self, *args, **kwargs):
        """Run method have to be overriden."""
        print("Run method for '{}' not implemented".format(self.named))
        return []


def python3(file, args=[]):
    if args:
        return 'python3 {} {}'.format(file, ' '.join([str(arg) for arg in args]))
    else:
        return 'python3 {}'.format(file)


def load_output(results):
    if results['Code'] == '0':
        try:
            var = json.loads(results['Stdout'])
        except Exception as e:
            raise Exception('JSON load failed: {}'.format(e))
    else:
        raise Exception('Operation failed: {}'.format(results['Stderr']))
    return var
