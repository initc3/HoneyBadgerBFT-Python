import logging

from logutils.colorize import ColorizingStreamHandler

import pytest


def pytest_collection_modifyitems(config, items):
    if config.getoption('-m') == 'demo':
        # do not skip demo tests
        return
    skip_demo = pytest.mark.skip(reason='need "-m demo" option to run')
    for item in items:
        if 'demo' in item.keywords:
            item.add_marker(skip_demo)


class BadgerColoredLogs(ColorizingStreamHandler):

    nodeid_map = {
        0: (None, 'green', False),
        1: (None, 'cyan', False),
        2: (None, 'blue', False),
        3: (None, 'magenta', False),
    }

    def colorize(self, message, record):
        """
        Colorize a message for a logging event.

        This implementation uses the ``level_map`` class attribute to
        map the LogRecord's level to a colour/intensity setting, which is
        then applied to the whole message.

        :param message: The message to colorize.
        :param record: The ``LogRecord`` for the message.
        """
        if record.nodeid in self.nodeid_map:
            bg, fg, bold = self.nodeid_map[record.nodeid]
            params = []
            if bg in self.color_map:
                params.append(str(self.color_map[bg] + 40))
            if fg in self.color_map:
                params.append(str(self.color_map[fg] + 30))
            if bold:
                params.append('1')
            if params:
                message = ''.join((self.csi, ';'.join(params),
                                   'm', message, self.reset))
        return message


logging.basicConfig(
    format='node %(nodeid)s|round %(epoch)s> %(module)s:%(funcName)s (%(lineno)d) %(message)s',
    level=logging.DEBUG,
    handlers=[BadgerColoredLogs()],
)
