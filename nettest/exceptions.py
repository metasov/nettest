class Error(Exception):
    def __init__(self, msg='', retval=999):
        self.retval = retval
        super(Error, self).__init__(msg)

class ConfigReadError(Error):
    def __init__(self, msg='', retval=1):
        super(CondigReadError, self).__init__(msg, retval)

class InterfaceError(Error):
    def __init__(self, msg='', retval=2):
        super(InterfaceError, self).__init__(msg, retval)

class ExecutionError(Error):
    def __init__(self, msg='', retval=3):
        super(ExecutionError, self).__init__(msg, retval)
    
class TerminationError(Error):
    def __init__(self, msg='', retval=4):
        super(TerminationError, self).__init__(msg, retval)

class CannotAcquireIP(Error):
    def __init__(self, msg='', retval=5):
        super(CannotAcquireIP, self).__init__(msg, retval)

