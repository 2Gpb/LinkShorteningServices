class LinkError(Exception):
    pass


class LinkNotFoundError(LinkError):
    pass


class ShortCodeAlreadyExistsError(LinkError):
    pass


class LinkExpiredError(LinkError):
    pass


class AccessDeniedError(LinkError):
    pass


class ShortCodeGenerationError(LinkError):
    pass


class InvalidExpiresAtError(LinkError):
    pass
