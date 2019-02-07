import toml
import sys
from staticanalyser.shared.platform_constants import CONFIG_LOCATION
from staticanalyser.shared.setup import setup

# run the setup function to make sure that relevant dirs are in place before continuing
setup()

_CONFIG_ITEMS = toml.load(CONFIG_LOCATION)
__all__ = ['get_languages']


# CONFIG SUBFUNCTIONS
# I've decided this is the best way to be retreiving config items since it means the IDE will catch any typos
# and every config item that can be exposed to the code has to be done so programmatically. Using the sub functions
# to get the calling function name and using this to find the dictionary key makes expanding the available config
# items easier since it requires a single line of code that doesn't change between functions
def _get_config_item_from_dict(item_key):
    return _CONFIG_ITEMS[item_key]


def _get_config_item():
    config_key = sys._getframe(1).f_code.co_name[4:]
    print(config_key)
# CONFIG SUBFUNCTIONS END


# START OF CONFIG OPTIONS
def get_languages() -> object:
    return _get_config_item()
