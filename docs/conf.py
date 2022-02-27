import sys, os
import byoc
from pathlib import Path

## General

project = 'BYOC'
copyright = '2020, Kale Kundert'
version = byoc.__version__
release = byoc.__version__

master_doc = 'index'
source_suffix = '.rst'
templates_path = ['_templates']
exclude_patterns = ['_build']
default_role = 'any'

## Extensions

extensions = [
        'autoclasstoc',
        'sphinx.ext.autodoc',
        'sphinx.ext.autosummary',
        'sphinx.ext.viewcode',
        'sphinx.ext.intersphinx',
        'sphinx.ext.napoleon',
        'sphinx_rtd_theme',
        'sphinx_inline_tabs',
        'sphinx_copybutton',
]
intersphinx_mapping = { #
        'python': ('https://docs.python.org/3', None),
}
autosummary_generate = True
autodoc_default_options = {
        'exclude-members': '__dict__,__weakref__,__module__',
}
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = ['css/tweaks.css']
pygments_style = 'sphinx'

def remove_tabs_js(app, exc):
    # This javascript keeps the tabs in sync, e.g. assuming that they represent 
    # languages and that you'd always want to see the same one.  That doesn't 
    # apply at all in my case, and it seems like the easiest work-around is 
    # just to nuke the javascript altogether.
    if app.builder.format == 'html' and not exc:
        tabs_js = Path(app.builder.outdir) / '_static' / 'tabs.js'
        tabs_js.unlink()

def setup(app):
    app.connect('build-finished', remove_tabs_js)
