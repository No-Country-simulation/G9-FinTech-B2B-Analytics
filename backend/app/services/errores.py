class ErrorNegocio(Exception):
    status_code = 400

    def __init__(self, detalle: str) -> None:
        super().__init__(detalle)
        self.detalle = detalle


class NoEncontrado(ErrorNegocio):
    status_code = 404


class Conflicto(ErrorNegocio):
    status_code = 409

class Prohibido(ErrorNegocio):
    status_code = 403