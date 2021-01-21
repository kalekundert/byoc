# Changelog

<!--next-version-placeholder-->

## v0.13.0 (2021-01-21)
### Feature
* Rename App metaclass ([`7f52a35`](https://github.com/kalekundert/appcli/commit/7f52a35ffe2b2d970c85b96a56dcc97fa759ceee))

### Fix
* Only count first paragraph as part of brief ([`39d91d2`](https://github.com/kalekundert/appcli/commit/39d91d2ef052e929bc5a7487308dae65f28d8239))

## v0.12.0 (2021-01-11)
### Feature
* Add `@on_load` and remove `param(set=...)` ([`49b4e14`](https://github.com/kalekundert/appcli/commit/49b4e1439bb41da8e4f2f2941c76d42b8f2a71e5))

### Fix
* Don't compare to ignore unless necessary ([`bd70420`](https://github.com/kalekundert/appcli/commit/bd704204e7afe8c29b6cbdf028d8259a5f0f028a))

## v0.11.0 (2021-01-11)
### Feature
* Automatically dedent docopt usage text ([`25164d7`](https://github.com/kalekundert/appcli/commit/25164d7abf827fbcf25464aff6be397a53aa7fc0))

### Fix
* Allow params to be set to non-hashable values ([`9571c04`](https://github.com/kalekundert/appcli/commit/9571c04853d8a0dc7dd149850c8def30071b0810))

## v0.10.1 (2021-01-10)
### Fix
* Debug error message ([`5eded00`](https://github.com/kalekundert/appcli/commit/5eded004abdba1b613fbce9f1f13e089a3ed5528))

## v0.10.0 (2021-01-10)
### Feature
* Add support for mutable default values ([`88894b6`](https://github.com/kalekundert/appcli/commit/88894b698b0cf40f01d591d51175961b20518b39))
* Make `inherited_param` compatible with all param subclasses ([`c65272f`](https://github.com/kalekundert/appcli/commit/c65272fd803e39607ef60d37b1f1161331431a1a))
* Implement `inherited_param` ([`518e80c`](https://github.com/kalekundert/appcli/commit/518e80c5012ce55af6de37d83e2d97c143b01163))

### Fix
* Correctly handle unspecified docopt flags ([`30328c5`](https://github.com/kalekundert/appcli/commit/30328c51157a581b6d5291cbc20cf4fc23cb8b06))

### Documentation
* Outline the README file ([`e3cd57d`](https://github.com/kalekundert/appcli/commit/e3cd57d78936749c113fe0e66a70cfb57896589c))

## v0.9.0 (2021-01-09)
### Feature
* Treat cast=... as a default when a key list is given ([`4567ad5`](https://github.com/kalekundert/appcli/commit/4567ad5236143e7b9299aeeebe408be6687aacbd))

## v0.8.0 (2021-01-09)
### Feature
* Use mako to render docopt usage text ([`9780f98`](https://github.com/kalekundert/appcli/commit/9780f98449fbbca0d0ed8b42aefa57f4d7feb019))

## v0.7.0 (2021-01-08)
### Feature
* Allows keys to be arbitrary callables ([`87a0b9c`](https://github.com/kalekundert/appcli/commit/87a0b9ce73a08c816109bbbce522811ef8655cf0))

## v0.6.0 (2021-01-08)
### Feature
* Add an easy way to toggle boolean parameters ([`ea7ba89`](https://github.com/kalekundert/appcli/commit/ea7ba8980848a0f6c46f2d0f293769ff76490ad3))
* Add a metaclass for circumventing the constructor ([`3120f36`](https://github.com/kalekundert/appcli/commit/3120f3617ac3dad668e788ecc7ac2ca75e1cd136))
* Add callback for when parameter value is changed ([`3a37468`](https://github.com/kalekundert/appcli/commit/3a37468ac729e6d202c32059030a299bb386945d))

## v0.5.0 (2021-01-07)
### Feature
* Add callback for parameter access ([`7c3bcf5`](https://github.com/kalekundert/appcli/commit/7c3bcf50164b6cc8633cc39037d626abd8b724df))

## v0.4.0 (2021-01-07)
### Feature
* Cache parameter values ([`c320d9e`](https://github.com/kalekundert/appcli/commit/c320d9e56cfd01e965b6c48a2e68ff1496ff44c8))

## v0.3.0 (2021-01-07)
### Feature
* Allow multiple keys to be associated with a single config ([`556dfa4`](https://github.com/kalekundert/appcli/commit/556dfa420dff1b354f0d5f322d8b8a5747afb61a))
* Add a reload() function ([`5fdde1f`](https://github.com/kalekundert/appcli/commit/5fdde1f8221d31479a5b77685cf60ebe7a084904))
* Allow layer locations to be callables ([`ad5ad16`](https://github.com/kalekundert/appcli/commit/ad5ad16845da3ecebfe07ed5aa787634d560594c))
* Allow not_found() to take any iterable type ([`507c133`](https://github.com/kalekundert/appcli/commit/507c133ff0122dce45ccc0742cd166426c877daa))
* Print all docopt messages to stderr ([`3737b3a`](https://github.com/kalekundert/appcli/commit/3737b3af634aed54780a184679e3b69245fd1103))
* Export the lookup() function ([`9694681`](https://github.com/kalekundert/appcli/commit/9694681a33852005a48a6c609ba12af6bd56b213))
* Teach make_map() about elipses ([`9c11385`](https://github.com/kalekundert/appcli/commit/9c11385b5a6afed620d6d8ca847fba01dda5844d))
* Add ignore argument ([`476b114`](https://github.com/kalekundert/appcli/commit/476b11459a83e8d168c3000f14e88b9e1158a57f))

### Fix
* Remove debug calls ([`04401f6`](https://github.com/kalekundert/appcli/commit/04401f649bb832cdd0c7829779dff684b1488783))

## v0.2.0 (2020-12-21)
### Feature
* Use classes for grouping; add CompositeConfig and CallbackConfig ([`751630f`](https://github.com/kalekundert/appcli/commit/751630fba26ff1c3ee63966f098886203efe2012))

### Fix
* Exclude inactive layers when looking up parameter values ([`6b1433c`](https://github.com/kalekundert/appcli/commit/6b1433ca9765d6814043cd2092d7c8ee1a9ba8bf))

## v0.1.0 (2020-12-07)
### Feature
* Add ArgparseConfig ([`6594f3c`](https://github.com/kalekundert/appcli/commit/6594f3c99844825d285828ae37f3dbcc6cda05c7))

### Documentation
* Add a brief description of the project ([`10e46e2`](https://github.com/kalekundert/appcli/commit/10e46e25f27c61e767dd252d9aa8cca177051ae5))
