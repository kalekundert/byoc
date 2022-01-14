#!/usr/bin/env python3

from .. import model
from ..model import _is_selected_by_cls
from ..errors import NoValueFound, Log
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

        log = Log()
        log.info("getting '{attr}' config_attr for {obj!r}", obj=obj, attr=self.name)

        for config in configs:
            if not _is_selected_by_cls(config, self.config_cls):
                log.info("skipped {config}: not derived from {config_cls.__name__}", config=config, config_cls=self.config_cls)
                continue

            try:
                return getter(config)
            except AttributeError as err:
                log.info(
                        "skipped {config}: {getter} raised {err.__class__.__name__}: {err}"
                            if self.getter else "skipped {config}: {err}",
                        config=config, getter=getter, err=err,
                )
                continue

        raise NoValueFound("can't find config attribute", log)
