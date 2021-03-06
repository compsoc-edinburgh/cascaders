'''
Set of code that is not dependant on the gui and is intented to provide
the model for the main interaction with the server. The main class that
should be used is the CascaderModel class. The other classes are mainly
helper classes
'''
from logging import debug, warn, error

import service
import client

from util import CallbackMixin

#-------------------------------------------------------------------------------
#constants
PORT = 5010
HOST = 'www.comp-soc.com'
#-------------------------------------------------------------------------------

class CascadersData(object):
    ''' Manages the list of cascaders and provides lookup functions '''

    def __init__(self, locator, username):
        '''
        locator is a object that implements labFromHostname.

        username -  the current users username. This is (optionally) excluded
        from results so that you are never displayed as a cascader
        '''
        self.locator = locator
        self.username = username
        self.cascaders = {}

    def __str__(self):
        return str(self.cascaders)

    def addCascader(self, username, host, subjects):
        '''
        >>> cd = CascadersData(None, 'me')
        >>> cd.addCascader('remote', 'remotehost', ['subject'])
        >>> cd.findCascader(username='remote')
        ('remote', ('remotehost', set(['subject'])))

        Key is on the username...
        >>> cd = CascadersData(None, 'me')
        >>> cd.addCascader('remote', 'remotehost', ['subject'])
        >>> cd.addCascader('remote', 'otherhost', ['subject'])
        >>> cd.findCascader(username='remote')
        ('remote', ('otherhost', set(['subject'])))

        Subjects are a set
        >>> cd = CascadersData(None, 'me')
        >>> cd.addCascader('remote', 'remotehost', ['a', 'a', 'b'])
        >>> cd.findCascader(username='remote')
        ('remote', ('remotehost', set(['a', 'b'])))
        '''
        try:
            _, curSubjects = self.cascaders[username]
            self.cascaders[username] = (host, set(subjects) | curSubjects)
        except KeyError:
            self.cascaders[username] = (host, set(subjects))

    def removeCascader(self, username):
        try:
            del self.cascaders[username]
        except KeyError:
            warn('Cascader that left didn\'t exist')

    def addCascaderSubjects(self, username, subjects):
        '''
        Adding the same subject again is fine
        >>> cd = CascadersData(None, 'me')
        >>> cd.addCascader('remote', 'remotehost', ['a'])
        >>> cd.addCascaderSubjects('remote', ['a'])
        >>> cd.findCascader(username='remote')
        ('remote', ('remotehost', set(['a'])))

        >>> cd = CascadersData(None, 'me')
        >>> cd.addCascader('remote', 'remotehost', [])
        >>> cd.addCascaderSubjects('remote', ['a'])
        >>> cd.findCascader(username='remote')
        ('remote', ('remotehost', set(['a'])))
        '''
        try:
            host, curSubjects = self.cascaders[username]
            self.cascaders[username] = (host, curSubjects | set(subjects))
        except KeyError:
            warn('Cascader (%s) that added subjects '
                 'didn\'t exist' % username)
            self.cascaders[username] = (None, set(subjects))

    def removeCascaderSubjects(self, username, subjects):
        debug('Cascader %s removed subjects %s' % (username, subjects))
        try: 
            host, curSubjects = self.cascaders[username]
            self.cascaders[username] = host, curSubjects - set(subjects)
        except KeyError:
            warn('Tried to remove subjects from cascader %s, '
                 'prob not cascading' % username)

    def findCascaders(self, lab=None, subjects=None, host=None,
                            includeMe=False):
        '''
        Find all cascaders that match the given patterns, although
        this will not return any cascaders that are not cascading in 
        any subjects

        includeMe - Include the user (if the user is cascading) in results

        TODO really slow, not sure it matters

        >>> cd = CascadersData(None, 'me')
        >>> cd.addCascader('remote', 'remotehost', [])
        >>> cd.findCascader(username='remote')
        '''
        for user, (cascHost, cascSubjects) in self.cascaders.iteritems():
            if len(cascSubjects) == 0:
                continue

            if includeMe == False and user == self.username:
                continue

            if host and host != cascHost:
                continue

            if lab and self.locator.labFromHostname(cascHost) != lab:
                continue

            if (subjects and
                    len(set(subjects).intersection(set(cascSubjects))) == 0):
                continue

            yield user, (host, cascSubjects)

    def findCascader(self, username=None, includeMe=False, **kwargs):
        ''' Wrapper around findCascaders, returns the first match or None '''
        if username is not None:
            if len(kwargs):
                error('Username not supported with other args')
                return None
            try:
                host, subjects = self.cascaders[username]
                if len(subjects) == 0: 
                    return None
                if includeMe == False and username == self.username:
                    return None
                return username, (host, subjects)
            except KeyError:
                warn('Couldn\'t find cascader with username: ' % username)
                return None

        try:
            return self.findCascaders(includeMe=includeMe, **kwargs).next()
        except StopIteration:
            return None

#-------------------------------------------------------------------------------

class CascaderModel(CallbackMixin):
    '''
    This is the model for the main interface, it holds and provides most of the
    data for cascaders. It doesn't handle conversations

    Data communication is done through callbacks. Which are either registered
    using the methods in this class or in the case of calls to the server
    they are added to the deferred result.
    '''
    def __init__(self, locator, username, hostname):
        CallbackMixin.__init__(self)

        self.cascaders = CascadersData(locator, username)

        self.service = s = service.RpcService()
        self.client = client.RpcClient(self.service, HOST,
                                       PORT, username, hostname)

        s.registerOnCascaderRemovedSubjects(self._onCascaderRemovedSubjects)
        s.registerOnCascaderAddedSubjects(self._onCascaderAddedSubjects)

        s.registerOnCascaderJoined(self._onCascaderJoined)
        s.registerOnCascaderLeft(self._onCascaderLeft)

        s.registerUserAskingForHelp(self._onUserAskingForHelp)

        self.registerOnLogin(self._onLogin)

        self.subjects = set()
        self.cascadeSubjects = set()
        self.cascading = False

        self.username = username
        self.hostname = hostname

    def __getattribute__(self, name):
        ''' 
        Both the client and the service have the ability to register some
        callbacks, this allows those callbacks to be used without
        having to expose anything beyond this class
        '''
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            if name.startswith('register'):
                if hasattr(self.client, name):
                    return self.client.__getattribute__(name)
                elif hasattr(self.service, name):
                    return self.service.__getattribute__(name)
            raise

    def getCascaderData(self):
        return self.cascaders
    #--------------------------------------------------------------------------
    # Service callbacks
    # These are setup in the __init__ function so that the service (interface
    # from server -> client) will call these when events occur
    # For the most part these are just passed on upwards, maybe taking into
    # account changes of data
    def _onCascaderAddedSubjects(self, username, subjects):
        debug('Cascader %s added subjects %s' % (username, subjects))
        self.cascaders.addCascaderSubjects(username, subjects)
        self._callCallbacks('cascaderschanged', self.cascaders)

    def _onCascaderRemovedSubjects(self, username, subjects):
        debug('Cascader %s removed subjects %s' % (username, subjects))
        self.cascaders.removeCascaderSubjects(username, subjects)
        self._callCallbacks('cascaderschanged', self.cascaders)

    def _onCascaderJoined(self, username, hostname, subjects):
        debug('New cascader: (%s, (%s, %s)' % (username,
                                               hostname,
                                               str(subjects)))
        self.cascaders.addCascader(username, hostname, subjects)
        self._callCallbacks('cascaderschanged', self.cascaders)

    def _onCascaderLeft(self, username):
        debug('Cascader left: %s' % username)
        self.cascaders.removeCascader(username)
        self._callCallbacks('cascaderschanged', self.cascaders)

    def _onUserAskingForHelp(self,  helpid, username, host,
                            subject, description):
        result = self._callCallbacks('userasking', helpid, username,
                                     host, subject, description)
        if len(result):
            return result[0]
    #--------------------------------------------------------------------------
    def registerOnCascaderChanged(self, function):
        self._addCallback('cascaderschanged', function)

    def registerOnSubjectChanged(self, function):
        self._addCallback('subjectschanged', function)

    def registerOnUserAskingForHelp(self, function):
        self._addCallback('userasking', function)
    #--------------------------------------------------------------------------

    def connect(self):
        debug('Connecting...')
        return self.client.connect()

    def login(self):
        debug('Logging in...')
        def subject(result):
            debug('Got subjects from login')
            self.subjects = set([x for x in result])
            self._callCallbacks('subjectschanged', self.subjects)

        def casc(result):
            debug('Got cascaders from login: %s' % str(result))
            for usr, host, sub in result:
                self.cascaders.addCascader(usr, host, sub)
            self._callCallbacks('cascaderschanged', self.cascaders)

        sl = lambda *a: self.client.getSubjectList().addCallback(subject)
        cl = lambda *a: self.client.getCascaderList().addCallback(casc)

        d = self.client.login()
        d.addCallback(cl)
        d.addCallback(sl)

        return d

    def _onLogin(self, *a):
        '''
        This tries for force everything to the way it was before
        the server disconnected
        '''
        debug('Now logged in, trying to restore settings')
        if self.isCascading():
            self.startCascading()
        self.addSubjects(self.cascadeSubjects)

    #--------------------------------------------------------------------------
    def isCascading(self):
        return self.cascading

    def startCascading(self):
        self.cascading = True
        return self.client.startCascading()

    def stopCascading(self):
        self.cascading = False
        return self.client.stopCascading()

    #--------------------------------------------------------------------------
    def cascadingSubjects(self):
        return self.cascadeSubjects

    def addSubjects(self, subjects):
        '''
        This doesn't try to mimize data transfer by checking
        subjects are valid as we may not have retrived the
        subjects by the time this is called
        '''
        self.cascadeSubjects = self.cascadeSubjects | set(subjects)
        debug('Adding subjects: %s' % str(subjects))
        return self.client.addSubjects(subjects)

    def removeSubjects(self, subjects):
        self.cascadeSubjects = self.cascadeSubjects - set(subjects)
        return self.client.removeSubjects(subjects)

    def askForHelp(self, helpid, username, subject, problem):
        return self.client.askForHelp(helpid, username, subject, problem)

    def sendMessage(self, helpid, toUsername, message):
        '''
        This shouldn't really be here I don't think. It isn't abstract enough
        '''
        return self.client.sendMessage(helpid, toUsername, message)

    def logout(self):
        return self.client.logout()
