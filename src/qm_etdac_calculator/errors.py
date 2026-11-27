"""Exceptions of the qm_etdac_calculator program."""

FORMAT_HINT = "(see docs/input-format.md)"  # appended to input-format errors


class InputError(ValueError):
    """
    The input files are invalid (ADR 0003, ADR 0005).

    Raised on purpose by the readers and validators, never for program bugs. The CLI
    prints the message as one clean line with a non-zero exit code; messages show
    untrusted values only through logging_setup.untrusted().
    """


class OutputError(Exception):
    """
    The output location cannot be used safely (ADR 0003).

    Raised when the output folder is a file or a symbolic link, the output name is not
    allowed, or a result would be overwritten. Like InputError, the CLI prints it as one
    clean line; it is never raised for program bugs.
    """
