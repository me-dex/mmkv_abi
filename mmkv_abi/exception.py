class MakeMKVNotFound(RuntimeError):
    def __init__(self):
        super().__init__('makemkvcon not found in PATH')

class ABIVersionMismatch(RuntimeError):
    def __init__(self):
        super().__init__('ABI version does not match requested version')

class CommunicationError(RuntimeError):
    def __init__(self):
        super().__init__('Communication error has occured. This may be a parsing issue')
