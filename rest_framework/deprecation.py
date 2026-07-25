class RemovedInDRF319Warning(DeprecationWarning):
    pass


class RemovedInDRF320Warning(PendingDeprecationWarning):
    pass


RemovedInNextDRFVersionWarning = RemovedInDRF319Warning
RemovedAfterNextDRFVersionWarning = RemovedInDRF320Warning
