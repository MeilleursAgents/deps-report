from deps_report.models import Dependency


def get_display_output_for_dependency(dependency: Dependency) -> str:
    properties = []
    if dependency.for_dev:
        properties.append("dev")
    if dependency.transitive:
        properties.append("transitive")

    if len(properties) == 0:
        return dependency.name

    return f"{dependency.name} ({','.join(properties)})"