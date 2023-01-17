# Customized error 509 exceptions.
class Error509(BaseException):
    pass


# Since e-hentai updates the gallery links in the favorites, the following code is useless
# class FailedFetchAPI(BaseException):
#     pass
