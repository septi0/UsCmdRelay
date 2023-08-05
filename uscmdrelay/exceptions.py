class GracefulExit(BaseException):
    pass

class UsCMdRelayConfigError(Exception):
    pass

class ClientRequestError(Exception):
    pass

# raise processError(message, code)
class ProcessError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code
