******
AppCLI
******

.. image:: https://img.shields.io/pypi/v/appcli.svg
   :target: https://pypi.python.org/pypi/appcli

.. image:: https://img.shields.io/pypi/pyversions/appcli.svg
   :target: https://pypi.python.org/pypi/appcli

.. image:: https://img.shields.io/readthedocs/appcli.svg
   :target: https://appcli.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/github/workflow/status/kalekundert/appcli/Test%20and%20release/master
   :target: https://github.com/kalekundert/appcli/actions

.. image:: https://img.shields.io/coveralls/kalekundert/appcli.svg
   :target: https://coveralls.io/github/kalekundert/appcli?branch=master

Library for making command line apps.  It's philosophy is that (i) it should be 
easy to incorporate options form the command line and config files, and (ii) 
the object should remain usable as a normal object in python.  For example::

    import appcli
    from appcli import DocoptConfig, AppDirsConfig, Key


    # Inheriting from App will give us the ability to instantiate MyApp objects 
    # without calling the constructor, i.e. exclusively using information from 
    # the command-line and the config files.  We'll take advantage of this in 
    # the '__main__' block at the end of the script:

    class MyApp(appcli.App):
        """
    Do a thing.

    Usage:
        myapp <x> [-y]
    """
        
        # The `__config__` class variable defines locations to search for 
        # parameter values.  In this case, we specify that `docopt` should be 
        # used to parse command line arguments, and that `appdirs` should be 
        # used to find configuration files.  Note however that appcli is not 
        # tied to any particular command-line argument parser or file format.  
        # A wide variety of `Config` classes come with `appcli`, and it's also 
        # easy to write your own.

        __config__ = [
                DocoptConfig(),
                AppDirsConfig(),
        ]
        
        # The `appcli.param()` calls define attributes that will take their 
        # value from the configuration source specified above.  For example, 
        # the `x` parameter will look for an argument named `<x>` specified on 
        # the command line.  The `y` parameter is similar, but will also (i) 
        # look for a value in the configuration files if none if specified on 
        # the command line, (ii) convert the value to an integer, and (iii) use 
        # a default of 0 if no other value is found.

        x = appcli.param(
                Key(DocoptConfig, '<x>'),
        )
        y = appcli.param(
                Key(DocoptConfig, '-y'),
                Key(AppDirsConfig, 'y'),
                cast=int,
                default=0,
        )

        # Define a constructor because we want this object to be fully usable 
        # from python.  Because <x> is a required argument on the command line, 
        # it makes sense for it to be a required argument to the constructor as 
        # well.

        def __init__(self, x):
            self.x = x

        # Define one or more methods that actually do whatever this application 
        # is supposed to do.  These methods can be named anything; think of 
        # MyApp as a totally normal class by this point.  Note that `x` and `y` 
        # can be used exactly like regular attributes.

        def main(self):
            return self.x * self.y

    # Invoke the application from the command line.  Note that we can't call 
    # the constructor because it requires an `x` argument, and we don't have 
    # that information yet (because it will come from the command line).  
    # Instead we use the `from_params()` method provided by `appcli.App`.  This 
    # constructs an instance of MyApp without calling the construtor, instead 
    # depending fully on the command-line and the configuration files to 
    # provide values for every parameter.  The call to `appcli.load()` triggers 
    # the command line to be parsed, such that the `app` instance is fully 
    # initialized when the `main()` method is called.

    if __name__ == '__main__':
        app = Main.from_params()
        appcli.load(app)
        app.main()

Note that we could seamlessly use this object in another python script::

    from myapp import MyApp

    # Because we don't call `appcli.load()` in this script, the command line 
    # would not be parsed.  The configuration files would still be read, 
    # however.  In the snippet below, for example, the value of `app.y` could 
    # come from the configuration file.  See `Config.autoload` for more 
    # information on controlling which configs are used in which contexts.

    app = MyApp('abc')
    app.main()
