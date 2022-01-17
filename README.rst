********************************
``byoc`` — Build Your Own Config
********************************

.. image:: https://img.shields.io/pypi/v/byoc.svg
   :target: https://pypi.python.org/pypi/byoc

.. image:: https://img.shields.io/pypi/pyversions/byoc.svg
   :target: https://pypi.python.org/pypi/byoc

.. image:: https://img.shields.io/readthedocs/byoc.svg
   :target: https://byoc.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/github/workflow/status/kalekundert/byoc/Test%20and%20release/master
   :target: https://github.com/kalekundert/byoc/actions

.. image:: https://img.shields.io/coveralls/kalekundert/byoc.svg
   :target: https://coveralls.io/github/kalekundert/byoc?branch=master

BYOC is a python library for loading configuration values from any number/kind 
of sources, e.g. files, command-line arguments, environment variables, remote 
JSON APIs, etc.  The primary goal of BYOC is to give you complete control over 
your configuration.  This means:

- Complete control over how things are named and organized.

- Complete control over how values from different config sources are merged.

- Support for any kind of file format, argument parsing library, etc.

- No opinions about anything enforced by BYOC.

The basic idea is to create a class with special attributes that know where to 
look for configuration values.  When these attributes are accessed, the correct 
values are looked up, possibly merged, possibly cached, and returned.  Here's a 
brief example to show what this looks like::

    import byoc
    from byoc import Key, DocoptConfig, AppDirsConfig

    class Greet(byoc.App):
        """
    Say a greeting.

    Usage:
        greet <name> [-g <greeting>]
    """
        # Define which config sources are available to this class.
        __config__ = [
                DocoptConfig,
                AppDirsConfig.setup(name='conf.yml'),
        ]

        # Define how to search for each config value.
        name = byoc.param(
                Key(DocoptConfig, '<name>'),
        )
        greeting = byoc.param(
                Key(DocoptConfig, '-g'),
                Key(AppDirsConfig, 'greeting'),
                default='Hello',
        )

        def main(self):
            self.load(DocoptConfig)
            print(f"{self.greeting}, {self.name}!")

    if __name__ == '__main__':
        Greet.entry_point()

We can configure this script from the command line::

  $ ./greet 'Sir Bedevere'
  Hello, Sir Bedevere!
  $ ./greet 'Sir Lancelot' -g Goodbye
  Goodbye, Sir Lancelot!

We can also configure this script via its configuration files::

  $ mkdir -p ~/.config/greet
  $ echo "greeting: Run away" > ~/.config/greet/conf.yml
  $ greet 'Sir Robin'
  Run away, Sir Robin!

This example only scratches the surface, but hopefully you can already get a 
sense for how powerful and flexible this property-based approach is.  For more 
information, refer to the following examples (in lieu of complete 
documentation).

Examples
========
For some examples of ``byoc`` being used in real scripts, check out the 
`Stepwise — Molecular Biology`__ repository.  Almost every script in this 
repository uses ``byoc``.  Below are some particular scripts that might be 
useful:

Simple scripts:

- `aliquot.py <https://github.com/kalekundert/stepwise_mol_bio/blob/master/stepwise_mol_bio/aliquot.py>`_
- `anneal.py <https://github.com/kalekundert/stepwise_mol_bio/blob/master/stepwise_mol_bio/anneal.py>`_
- `kld.py <https://github.com/kalekundert/stepwise_mol_bio/blob/master/stepwise_mol_bio/kld.py>`_

Long but straight-forward scripts:

- `pcr.py <https://github.com/kalekundert/stepwise_mol_bio/blob/master/stepwise_mol_bio/pcr.py>`_
- `spin_cleanup.py <https://github.com/kalekundert/stepwise_mol_bio/blob/master/stepwise_mol_bio/spin_cleanup.py>`_
- `gels/gel.py <https://github.com/kalekundert/stepwise_mol_bio/blob/master/stepwise_mol_bio/gels/gel.py>`_
- `gels/stain.py <https://github.com/kalekundert/stepwise_mol_bio/blob/master/stepwise_mol_bio/gels/stain.py>`_

Complex scripts:

- `serial_dilution.py <https://github.com/kalekundert/stepwise_mol_bio/blob/master/stepwise_mol_bio/serial_dilution.py>`_

  This script features parameters that depend on other parameters.  
  Specifically, the user must provide values for any three of ``volume``, 
  ``conc_high``, ``conc_low``, and ``factor``.  Whichever one isn't specified 
  is inferred from the ones that are.  This is implemented by making the 
  ``byoc`` parameters (which in this case read only from the command-line and 
  not from any config files) private, then adding public properties that are 
  calculated from the private ones.

- `digest.py <https://github.com/kalekundert/stepwise_mol_bio/blob/master/stepwise_mol_bio/digest.py>`_

  This script is actually pretty simple, but it makes used of 
  ``__bareinit__()`` to download some data from the internet.  As alluded to 
  above, ``__init__()`` is not called when ``App`` instances are initialized 
  from the command-line, because ``__init__()`` might require arbitrary 
  arguments and is therefore considered to be part of the python API.  Instead, 
  ``App`` instances are initialized by calling ``__bareinit__()`` with no 
  arguments.

- `ivtt.py <https://github.com/kalekundert/stepwise_mol_bio/blob/master/stepwise_mol_bio/ivtt.py>`_

  This script defines a custom ``Config`` class to read from a sequence 
  database. (This example might go out of date, though; I have plans to move 
  that custom ``Config`` into a different package.)

__ https://github.com/kalekundert/stepwise_mol_bio 
