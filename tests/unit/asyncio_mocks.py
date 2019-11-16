from unittest.mock import MagicMock
# from unittest.mock import AsyncMock as AsyncioMock
# from asyncio import Future
import asyncio


def loop(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def AsyncMock(*args, **kwargs):
    m = MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


def AsyncClassMethodMock(*args, **kwargs):
    m = MagicMock(*args, **kwargs)

    async def mock_coro(self, *args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


def AsyncClassMock(*args, static=[], props={}):
    """
    Async Class Mock.

    Provide names of mocked methods as args.
    """
    class mock_class(MagicMock):
        pass

    for item in args:
        setattr(mock_class, item, AsyncClassMethodMock())
    for item in static:
        setattr(mock_class, item, AsyncMock())
    for prop, value in props.items():
        setattr(mock_class, prop, value)
    return mock_class
