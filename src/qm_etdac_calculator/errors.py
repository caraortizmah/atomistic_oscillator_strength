"""Exceptions of the qm_etdac_calculator program."""


class InputError(ValueError):
    """
    The input files are invalid (ADR 0003, ADR 0005).

    Raised on purpose by the readers and validators, never for program bugs. The CLI
    prints the message as one clean line with a non-zero exit code; messages show
    untrusted values only through logging_setup.untrusted().
    """
