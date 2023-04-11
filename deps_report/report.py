import csv
import json
import logging
from collections import Counter
from pathlib import Path
from pprint import pprint
import pandas as pd

from deps_report.models import RuntimeInformations
from deps_report.models.results import VersionResult, VulnerabilityResult, ErrorResult


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

MA_PROD_APPS = [
    'agencyapi',
    'b2cleadrankingapi',
    'barometre',
    'barometreapi',
    'buffer',
    'carbon14',
    'connectapi',
    'de-estimamodels',
    'dvfapi',
    'estimaapi',
    'estimamodelsapi',
    'externaladmanagerapi',
    'feedbackapi',
    'filewatch',
    'ftp_auth',
    'geoapi',
    'indiceapi',
    'internaltoolsapi',
    'leadapi',
    'mailapi',
    'marketapi',
    'mediaapi',
    'myaccountapi',
    'myproapi',
    'passerelles',
    'pdfapi',
    'prospectionmapapi',
    'realtorexplorerapi',
    'salesforceapi',
    'soldpropertyapi',
    'thirdpartiesapi',
    'thumbor',
    'topofthelistapi',
    'userapi',
    'vectortileapi',
    'webanalytics',
    'www-flask',
]


class DepsResult:
    def __init__(self, out_json_path: Path):
        self.app_name = out_json_path.parent.name
        self._out_json = json.loads(file_path.read_text())
        self._version_results: list[dict] = self._out_json.get("version_results")
        self._vulnerabilities_result: list[dict] = self._out_json.get(
            "vulnerabilities_result"
        )
        self._errors_results: list[dict] = self._out_json.get("errors_results")
        self._runtime_informations: dict = self._out_json.get("runtime_informations")

    def _append_app_name(self, json_item):
        json_item.update({"app_name": self.app_name})
        return json_item

    @property
    def version_results_rows(self):
        for r in self._version_results:
            current_result = VersionResult.parse_obj(r)
            # do not add dev dependencies
            if current_result.dependency.for_dev:
                continue
            transformed = pd.json_normalize(r, sep="_").to_dict(orient="records")[0]
            transformed.pop("dependency_repositories")
            transformed.pop("dependency_version")
            # add column for outdated majors
            transformed.update(
                {"is_outdated_major": current_result.is_outdated_major()})
            yield self._append_app_name(transformed)

    @property
    def vulnerabilites_result_rows(self):
        for r in self._vulnerabilities_result:
            transformed = pd.json_normalize(r, sep="_").to_dict(orient="records")[0]
            transformed.pop("dependency_repositories")
            yield self._append_app_name(transformed)

    @property
    def runtime_informations_row(self):
        return self._append_app_name(self._runtime_informations)


class DepsResultExporter:
    def __init__(self):
        self.version_results_writer = self._init_writer(
            "version_results_export.csv",
            (
                "app_name",
                "dependency_name",
                "installed_version",
                "latest_version",
                "dependency_transitive",
                "dependency_for_dev",
                "is_outdated_major",
            ),
        )

        self.vulnerabilities_result_writer = self._init_writer(
            "vulnerabilities_results_export.csv",
            (
                "app_name",
                "dependency_name",
                "dependency_version",
                "advisory",
                "impacted_versions",
                "dependency_transitive",
                "dependency_for_dev",
            ),
        )

        self.runtime_informations_writer = self._init_writer(
            "runtime_informations_export.csv",
            (
                "app_name",
                "name",
                "current_version",
                "latest_version",
                "current_version_is_outdated",
                "current_version_eol_date",
                "current_version_is_eol_soon",
                "current_version_is_eol",
            ),
        )

    def _init_writer(self, filename: str, row_header: tuple = None):
        version_results_paths = Path(filename)
        writer = csv.DictWriter(version_results_paths.open("w"), row_header or ())
        writer.writeheader()
        return writer

    def append_result(self, deps_result: DepsResult):
        for row in deps_result.version_results_rows:
            self.version_results_writer.writerow(row)

        for row in deps_result.vulnerabilites_result_rows:
            self.vulnerabilities_result_writer.writerow(row)

        self.runtime_informations_writer.writerow(deps_result.runtime_informations_row)


if __name__ == "__main__":
    deps_reports_path = Path("ma-apps")
    report_dict = {}
    deps_exporter = DepsResultExporter()
    for file_path in deps_reports_path.rglob("out.json"):
        app_name = file_path.parent.name
        if app_name not in MA_PROD_APPS:
            continue
        logger.info(str(file_path))
        content = json.loads(file_path.read_text())
        named_content = {app_name: content}
        report_dict.update(named_content)

        result = DepsResult(file_path)
        deps_exporter.append_result(result)
        logger.info("done")

    # exit()
    vulnerabilities_result = {
        k: v.get("vulnerabilities_result") for k, v in report_dict.items()
    }
    vulnerabilities_count = Counter()
    for app_name, vulnerabilities in vulnerabilities_result.items():
        vulnerabilities_count.update(
            {d.get("dependency").get("name"): 1 for d in vulnerabilities}
        )

    versions_result = {k: v.get("version_results") for k, v in report_dict.items()}
    versions_counter = Counter()
    for app_name, versions in versions_result.items():
        versions_counter.update({app_name: len(versions)})

    versions_outdated_major_counter = Counter()
    for app_name, versions in versions_result.items():
        for version in versions:
            versions_result = VersionResult.parse_obj(version)
            if versions_result.is_outdated_major():
                versions_outdated_major_counter.update({app_name: 1})
    pprint(vulnerabilities_count.most_common())
    pprint(versions_counter.most_common())
    pprint(versions_outdated_major_counter.most_common())

    logger.info("done")
