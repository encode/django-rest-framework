class FunctionSimplicityCheckPy35Mixin:
    def get_good_cases(self):
        def annotated_simple() -> int:
            return 0

        def annotated_defaults(x: int = 0) -> int:
            return 0

        def kwonly_defaults(*, x=0):
            pass
        return super().get_good_cases() + (annotated_simple, annotated_defaults, kwonly_defaults)

    def get_bad_cases(self):
        def kwonly(*, x):
            pass

        return super().get_bad_cases() + (kwonly,)
