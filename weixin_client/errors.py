
class ClientError(Exception):
    def __init__(self, detail, *args, **kwargs):
        self.detail = detail


class InvaildMaterialError(ClientError):
    pass
