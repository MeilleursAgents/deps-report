from deps_report.models import DependencyRepository

DEFAULT_REPOSITORY = DependencyRepository(
    name="pypi",
    url="https://pypi.org/simple",
)
