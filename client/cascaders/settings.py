'''
Functions for dealing with settings files, the settings file is basically an
dict and this provides the functions for dealing with that dict
'''
import os
import shutil
import json
from logging import warn, debug

#List of default settings, if there are errors these are used
defaultSettings = {
        'autostart' : False,        #program autostart
        'cascSubjects' : [],        #list of cascading subjects
        'cascading' : False,        #is the user cascading
        'autocascade' : False,      #start cascading on program start?
        'asked_autocascade' : False,#asked if we should autocascade
        'asked_autostart' : False,  #asked if we should autostart
}

def getSettingsDirectory():
    ''' Gets the settings directory, will autocreate if it doesn't exist'''
    home = os.path.expanduser('~')
    dr = os.path.join(home, '.config', 'cascaders')
    if not os.path.exists(dr):
        debug('creating directoires for config')
        os.makedirs(dr)
    return dr

def getSettingsFile():
    return os.path.join(getSettingsDirectory(), 'settings.json')

def loadSettings():
    '''
    Tries to load the settings, if it fails, then the default settings
    are returned
    '''
    try:
        with open(getSettingsFile()) as fh:
            fileStr = fh.read()
            try:
                settings = json.loads(fileStr)
            except ValueError:
                warn('Failed to decode json, using default settings')
                return defaultSettings

            for k, v in defaultSettings.iteritems():
                if not k in settings:
                    settings[k] = v
            return settings
    except IOError:
        debug('Failed to open file, probably doesn\'t exist')
        return defaultSettings

def saveSettings(settings):
    _fixAutostartGnome(settings)
    with open(getSettingsFile(), 'wb') as f:
        return f.write(json.dumps(settings))


def _fixAutostartGnome(settings):
    '''
    This sorts autostart so that it should work on gnome, depenant on 
    the settings.
    '''
    home = os.path.expanduser('~')
    path = os.path.join(home, '.config', 'autostart', 'cascaders.desktop')
    if settings['autostart'] == False:
        if os.path.exists(path):
            os.remove(path)
    else:
        if not os.path.exists(path):
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(path)
            debug('Moving autostart file to %s' % path)
            fromPath = os.path.join(os.path.dirname(__file__),
                                    'data',
                                    'autostart.desktop')
            shutil.copy(fromPath, path)
