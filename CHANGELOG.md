# Changelog

<!--next-version-placeholder-->

## v0.29.0 (2022-01-19)
### Feature
* Add a JSON config ([`c8e461c`](https://github.com/kalekundert/byoc/commit/c8e461c22aff73f868322a37993ca3a038d24c60))
* Make a parent class for CLI configs ([`30f7567`](https://github.com/kalekundert/byoc/commit/30f75674bca565afb9f75c307cabf0394e7f11b9))

## v0.28.1 (2022-01-17)
### Fix
* Improve test coverage ([`2e8fa21`](https://github.com/kalekundert/byoc/commit/2e8fa212777468b0545a56cf28f80470f9c30598))

### Documentation
* Tweak wording ([`1385a2d`](https://github.com/kalekundert/byoc/commit/1385a2d6ecf023884cdcb5ae098c90c088aef588))

## v0.28.0 (2022-01-17)
### Feature
* Allow Config.autoload to be set from Config.setup() ([`9735986`](https://github.com/kalekundert/byoc/commit/97359866775639cce424b4430c69ab1d97f03182))

### Documentation
* Tweak title and example ([`73bb1fe`](https://github.com/kalekundert/byoc/commit/73bb1fe3bc52ceadddfb94d82a7f4c08c9537897))

## v0.27.0 (2022-01-17)
### Feature
* Rename 'attr' back to 'param' ([`2bc8e0b`](https://github.com/kalekundert/byoc/commit/2bc8e0b5e3b635ade5c69f28d681383967a758ec))

### Documentation
* Use a real m-dash ([`27cbfcb`](https://github.com/kalekundert/byoc/commit/27cbfcba0e95c4c1dcce3329fe514507820c7811))
* Improve the introduction ([`6501a6e`](https://github.com/kalekundert/byoc/commit/6501a6eda103a220ecb4721190269d9c32a8f8dc))

## v0.26.0 (2022-01-14)
### Feature
* Rename 'param' to 'attr' ([`30a37e7`](https://github.com/kalekundert/byoc/commit/30a37e7d111ad5e620ca44e74b1bf38a37bd0c80))
* Rename project to 'byoc' ([`0ca13b9`](https://github.com/kalekundert/byoc/commit/0ca13b9fe46d525fae24fcff19bb102b0267408a))
* Improve log messages for FileConfig ([`6628a19`](https://github.com/kalekundert/byoc/commit/6628a19ff1eee3e01d12b100a8996dffb022eb5c))
* Configure caching on a per-getter basis ([`75b540d`](https://github.com/kalekundert/byoc/commit/75b540d91727b0e9d6981ff5ae917fc1a4c59eb4))
* Expose metadata for each parameter ([`7c332ac`](https://github.com/kalekundert/byoc/commit/7c332acdadfe4842719d610144cb68d9dcec5c29))
* Forbid dotted keys ([`23efa74`](https://github.com/kalekundert/byoc/commit/23efa74e8adbfd74d5a4eba69fee67753ca8b5be))
* Always invoke param(cast=...) ([`f62ce56`](https://github.com/kalekundert/byoc/commit/f62ce56f4e2991b674e983b3ac4377f59f7dbb91))
* Be more conservative about exceptions ([`51a9a06`](https://github.com/kalekundert/byoc/commit/51a9a0635c1c19b066a5ef03a01be1ae419d0491))

### Documentation
* Describe why on-the-fly loading doesn't work ([`6099b42`](https://github.com/kalekundert/byoc/commit/6099b42d47de0ad9bc6c3b2b091396a99c8b126a))

## v0.25.0 (2022-01-11)
### Feature
* Add a main function to app classes ([`f7e865a`](https://github.com/kalekundert/appcli/commit/f7e865a4f2c4da4647c533fdd2040ec4cdc31b8a))
* Allow file configs to read multiple paths ([`eac2444`](https://github.com/kalekundert/appcli/commit/eac2444c576215c93408c1ddb1cd971522883307))

## v0.24.0 (2021-12-16)
### Feature
* Initialize file configs via setup() ([`5791e2f`](https://github.com/kalekundert/appcli/commit/5791e2f2f8a8e75f6810d2a6f9a57a7d6aaa894c))

### Fix
* Improve error message ([`77e1539`](https://github.com/kalekundert/appcli/commit/77e1539aecc2666a9563dedee5c68e7f0d52cecc))

## v0.23.0 (2021-06-28)
### Feature
* Provide a default __bareinit__() implementation ([`ef0242a`](https://github.com/kalekundert/appcli/commit/ef0242a57f6cb2aaa802cff2d33de21e32dd6dd3))
* Allow Func/Method getters to ignore exceptions ([`02391eb`](https://github.com/kalekundert/appcli/commit/02391ebcda04dbe6775a3f33a960370e1d96f0f4))
* Add configs to existing objects ([`28563b8`](https://github.com/kalekundert/appcli/commit/28563b87d918f5665353e8b6eaf7370fcf74e7c0))
* Support setup arguments for the CLI configs ([`2ce4420`](https://github.com/kalekundert/appcli/commit/2ce44205bf881d6c47e3550101538c7e4a51cd6c))
* Rename `Config.with_options` to `Config.setup` ([`c7778b6`](https://github.com/kalekundert/appcli/commit/c7778b645ae39349ddb7f8606cecfbd1d04ad0d4))
* Add a way to bind options to Config factories ([`03306de`](https://github.com/kalekundert/appcli/commit/03306de6088504da742f2a477a138a4ba1d98bd2))

### Fix
* Cache exceptions ([`f828ff8`](https://github.com/kalekundert/appcli/commit/f828ff86815010d016b8b2e75343cd91fc290582))
* `rtoml.load()` requires path objects, not strings ([`a8ef104`](https://github.com/kalekundert/appcli/commit/a8ef1044407b093baf24ee596bbb2fdcc006aa8c))
* Apply schema after root key ([`fe008dd`](https://github.com/kalekundert/appcli/commit/fe008dd46aad3fb33779b587e376209217748b6b))

## v0.22.0 (2021-06-21)
### Feature
* Allow instance-level Config callbacks ([`3f4eb8d`](https://github.com/kalekundert/appcli/commit/3f4eb8d3709df2415d5b82e252cbce33b1347b84))

### Documentation
* Reformat log message ([`4e7e173`](https://github.com/kalekundert/appcli/commit/4e7e1733269bfc16705cce2c90bf88053e142a55))

## v0.21.1 (2021-06-17)
### Fix
* Allow DictLayer 'values' argument to be positional ([`f0bea0e`](https://github.com/kalekundert/appcli/commit/f0bea0e8abca0f7dc6fd62fc984bacab7190696a))

## v0.21.0 (2021-06-17)
### Feature
* Instantiate new configs for each object ([`a70b2d6`](https://github.com/kalekundert/appcli/commit/a70b2d6be577f47cab33e18e1693177365c678cc))

## v0.20.0 (2021-06-16)
### Feature
* Log the attribute lookup process ([`de22e5a`](https://github.com/kalekundert/appcli/commit/de22e5abc01cfa5bd55018e65eaefcc9536cf85a))

## v0.19.2 (2021-06-01)
### Fix
* Use 'is' when comparing values to *ignore*. ([`41acd1d`](https://github.com/kalekundert/appcli/commit/41acd1dc78fe72b6f05d28af1be07d5ed8a27e5d))

## v0.19.1 (2021-05-19)
### Fix
* Allow falsy config keys ([`bd66fba`](https://github.com/kalekundert/appcli/commit/bd66fbada4e78386ced3b5cb42c37beeea3590fa))

## v0.19.0 (2021-04-26)
### Feature
* Try rtoml before falling back on toml ([`accf065`](https://github.com/kalekundert/appcli/commit/accf065efb60111e903e142fe645d3fdb1485cd7))

### Fix
* Add config_cls argument to app.load() ([`55ebe2a`](https://github.com/kalekundert/appcli/commit/55ebe2aeb3d8ed9b9db8a0868f2648d44ea54bae))

## v0.18.2 (2021-04-22)
### Fix
* Don't share bound getters between instances ([`2d72a0e`](https://github.com/kalekundert/appcli/commit/2d72a0e6d8a2b198c8439b834ea4749ea517601b))

### Documentation
* Organize README into sections ([`d674072`](https://github.com/kalekundert/appcli/commit/d6740725450c541b8102f104ee849d6be1feffce))
* Link to examples from stepwise_mol_bio ([`d45b44a`](https://github.com/kalekundert/appcli/commit/d45b44a8705036f5d2638d54c6d99afc9def2adf))

## v0.18.1 (2021-03-30)
### Fix
* Make layers mutable again ([`7b23c01`](https://github.com/kalekundert/appcli/commit/7b23c010b713182a258b8d98fc3475175ec19979))

### Documentation
* Fix doctest ([`6e0c25b`](https://github.com/kalekundert/appcli/commit/6e0c25b8d6f187325461c346f8194a74ed3c9698))

## v0.18.0 (2021-03-25)
### Feature
* Use `Getter` classes to pick values ([`aa18b52`](https://github.com/kalekundert/appcli/commit/aa18b525339048603d0f7d75b93add1b020b1232))

## v0.17.0 (2021-03-24)
### Feature
* Add `SelfConfig` ([`39e3f3b`](https://github.com/kalekundert/appcli/commit/39e3f3b6126e93892f005d66121143adb570ede8))
* Make it easier to compose cast functions ([`2ef93e2`](https://github.com/kalekundert/appcli/commit/2ef93e2899921bfa25bea0ccf76fe40b88cefad4))
* Force layer values to be collections ([`dd82715`](https://github.com/kalekundert/appcli/commit/dd827158a7d69b28ca2bfbc95b493a1d79845d2d))

## v0.16.0 (2021-03-05)
### Feature
* Make key names optional ([`3a50d13`](https://github.com/kalekundert/appcli/commit/3a50d13c0c32966dfb22155f3caba58a30da992d))
* Allow subkeys to be specified using tuples ([`ac970dc`](https://github.com/kalekundert/appcli/commit/ac970dc6d6587f0b294596d8b84cb92f60540011))
* Teach FileConfig to read paths from attributes ([`328544c`](https://github.com/kalekundert/appcli/commit/328544cdfac14d19455dcc4cb3b0f11499adceb9))

## v0.15.1 (2021-02-17)
### Fix
* Respect default cast argument when using Key() ([`0442d69`](https://github.com/kalekundert/appcli/commit/0442d6954ae86a58a0e4371f28ab48f5db3c1207))

## v0.15.0 (2021-02-17)
### Feature
* Add an environment variable config ([`3c89019`](https://github.com/kalekundert/appcli/commit/3c89019d316727aecff319d982e6c012eca1ce8f))

## v0.14.0 (2021-02-17)
### Feature
* Allow parameters to control config order ([`12b8656`](https://github.com/kalekundert/appcli/commit/12b86563ebed29644533fd7ee895ae955bb26e87))
* Add convenience methods to load/reload app objects ([`f07de2b`](https://github.com/kalekundert/appcli/commit/f07de2b10fa88679535cd737fb4ea335dafb0268))
* Improve error reporting for mako templates ([`853f8b9`](https://github.com/kalekundert/appcli/commit/853f8b95f6345d9074cca820d4ea246a43f3f008))

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
