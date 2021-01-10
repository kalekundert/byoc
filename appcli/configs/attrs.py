#!/usr/bin/env python3

from .. import model
from ..errors import AppcliError, ConfigError

class config_attr:

    def __init__(self, key=None):
        self.key = key

    def __set_name__(self, cls, name):
        self.name = name

    def __get__(self, obj, cls=None):
        attr = self.key or self.name
        configs = model.get_configs(obj)

        with AppcliError.add_info(
                "getting '{attr}' config_attr for {obj!r}",
                obj=obj,
                attr=attr,
        ):
            for config in configs:
                try:
                    getter = getattr(config, f'get_{attr}')
                except AttributeError:
                    pass
                else:
                    return getter(obj)

            err = ConfigError(
                    configs=configs,
            )
            err.brief = "can't find config attribute"
            err.info += lambda e: "\n".join([
                    "the following config objects were queried:",
                    *(repr(x) for x in e.configs),
            ])
            raise err
