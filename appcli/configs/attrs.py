#!/usr/bin/env python3

from .. import model
from ..model import _is_selected_by_cls
from ..errors import AppcliError, ConfigError
from operator import attrgetter

class config_attr:

    def __init__(self, config_cls=None, *, getter=None):
        self.config_cls = config_cls
        self.getter = getter

    def __set_name__(self, cls, name):
        self.name = name

    def __get__(self, obj, cls=None):
        model.init(obj)

        configs = [x.config for x in model.get_wrapped_configs(obj)]
        getter = self.getter or attrgetter(self.name)

        with AppcliError.add_info(
                "getting '{attr}' config_attr for {obj!r}",
                obj=obj,
                attr=self.name,
        ):
            err = ConfigError(
                    configs=configs,
                    config_cls=self.config_cls,
                    getter=getter,
            )

            for config in configs:
                if not _is_selected_by_cls(config, self.config_cls):
                    err.put_info("skipped {config}: not derived from {config_cls.__name__}", config=config)
                    continue

                try:
                    return getter(config)
                except AttributeError as err2:
                    err.put_info(
                            "skipped {config}: {getter} raised {err.__class__.__name__}: {err}" if self.getter else
                            "skipped {config}: {err}",
                            config=config, err=err2,
                    )
                    continue

            err.brief = "can't find config attribute"
            raise err
