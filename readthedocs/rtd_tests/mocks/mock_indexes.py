"""Mock for search api of Index-es."""


class MockIndex(object):
    def search(self, body, **kwargs):
        kwargs.update({'body': body})
        return kwargs

    def __call__(self):
        return self
