import os
import gtk

from logging import debug

class AcceptHelpDialog():
    '''
    This is the dialog that comes up asking if the cascader wants to accept
    the help from the user. This is relativly dumb class

    It is used by the CascaderFrame class
    '''

    def __init__(self, parentWindow, username, subject, description):
        builder = gtk.Builder()

        dr = os.path.dirname(__file__)
        builder.add_from_file(os.path.join(dr, 'gui', 'helpacceptreject.glade'))

        self.window = builder.get_object('dgHelpAcceptReject')
        if parentWindow is not None:
            self.window.set_transient_for(parentWindow)

        heading = '%s is wanting help on %s' % (username, subject)
        builder.get_object('lbUserInfo').set_label(heading)
        builder.get_object('lbDesc').set_label(description)
        builder.connect_signals(self)

        self.accept = True

        self.window.show_all()
        self.window.run()

    def _onReject(self, e):
        self.accept = False
        self.window.destroy()

    def _onAccept(self, e):
        debug('Cascader accepted')
        self.accept = True
        self.window.destroy()

    #--------------------------------------------------------------------------
    # Functions for external use

    def isAccept(self):
        return self.accept


