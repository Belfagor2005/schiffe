# -*- coding: utf-8 -*-

import gettext
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

__version__ = "7.1.1"

PluginLanguageDomain = "Schiffe"
PluginLanguagePath = "Extensions/Schiffe/locale"


def localeInit():
    if PluginLanguageDomain and PluginLanguagePath:
        gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
    translated = gettext.dgettext(PluginLanguageDomain, txt)
    if translated:
        return translated
    else:
        print("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt))
        return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)
