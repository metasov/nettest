from ConfigParser import (SafeConfigParser,
                          NoSectionError,
                          NoOptionError)
from nettest.exceptions import ConfigReadError

class NettestConfig(SafeConfigParser):
    def get(self, full_name, default=None):
        """Get option from config.
        
        :param full_name: string in format "section_name.option_name"
        """
        section, option = full_name.split('.')
        try:
            result = SafeConfigParser.get(self, section, option)
        except NoSectionError:
            if default is not None:
                return default
            raise ConfigReadError(
                'Error reading %s from config. Section %s not found.',
                full_name, section)
        except NoOptionError:
            if default is not None:
                return default
            raise ConfigReadError(
                'Error reading %s from config. Option %s not found.',
                full_name, option)
        return result

    def getint(self, full_name, default=None):
        assert default is None or isinstance(default, int)
        result = self.get(full_name, default)
        try:
            result = int(result)
        except (ValueError, TypeError):
            raise ConfigReadError(
                'Error reading %s from config. '
                'Integer expected, found %s',
                full_name, repr(result))
        return result

