class I18nBinder:
    def __init__(self):
        self._bindings = []

    def __call__(self, setter, value_getter):
        self._bindings.append((setter, value_getter))
        return value_getter()

    def update(self):
        for setter, value_getter in self._bindings:
            setter(value_getter())
