class MyfitnesspalError(Exception):
    pass


class MyfitnesspalRequestFailed(MyfitnesspalError):
    pass


class MyfitnesspalLoginError(MyfitnesspalError, ValueError):
    pass
