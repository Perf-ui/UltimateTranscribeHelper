"""Run the existing CLI in a separate process from the desktop interface."""
import multiprocessing
import logging
import os
import warnings


class _HideTensorFlowDeprecations(logging.Filter):
    """Keep useful runtime warnings while hiding legacy API migration notices."""

    def filter(self, record):
        return not (record.levelno == logging.WARNING and "deprecated" in record.getMessage().lower())


def main():
    multiprocessing.freeze_support()
    warnings.filterwarnings("ignore", message=r"pkg_resources is deprecated as an API.*", category=UserWarning)
    # Windows feature extraction launches child interpreters; propagate the
    # same narrowly scoped filter to those workers.
    warning_filter = "ignore:pkg_resources is deprecated as an API:UserWarning"
    os.environ["PYTHONWARNINGS"] = ",".join(filter(None, (os.environ.get("PYTHONWARNINGS"), warning_filter)))
    logging.getLogger("tensorflow").addFilter(_HideTensorFlowDeprecations())
    from omnizart.cli.cli import entry
    entry()


if __name__ == "__main__":
    main()
