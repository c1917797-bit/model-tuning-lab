#!/usr/bin/env python3
"""Unified command-line entry point for Huawei-style presentation production."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from workflow_common import DEFAULT_CATALOG, DEFAULT_TEMPLATE, SKILL_ROOT, read_json, resolve_project, write_json


PROJECT_DIRS = ["work", "design-prompts", "design-drafts", "editable-run", "qa", "final"]
VISUAL_FIDELITY_CHECKS = (
    "visual_semantics_preserved",
    "region_geometry_preserved",
    "density_preserved",
    "distinct_views_and_states_preserved",
    "complex_assets_not_approximated",
    "icon_language_consistent",
    "typography_hierarchy_preserved",
)


def command_init(args: argparse.Namespace) -> int:
    out = Path(args.out).expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit("Output directory is not empty: %s" % out)
    out.mkdir(parents=True, exist_ok=True)
    for folder in PROJECT_DIRS:
        (out / folder).mkdir(parents=True, exist_ok=True)
    brief_arg = Path(args.brief).expanduser()
    brief_text = brief_arg.read_text(encoding="utf-8") if brief_arg.exists() else args.brief
    (out / "brief.md").write_text(brief_text.rstrip() + "\n", encoding="utf-8")
    (out / "outline.md").write_text(
        "# Presentation Outline\n\nStatus: DRAFT - awaiting one-time user approval\n\n",
        encoding="utf-8",
    )
    write_json(out / "deck_spec.json", {"schema_version": 1, "deck_name": out.name, "slides": []})
    write_json(out / "project.json", {
        "schema_version": 1,
        "skill": "tech-company-report-ppt",
        "outline_approved": False,
        "stage": "outline",
    })
    print(json.dumps({"project": str(out), "stage": "outline"}, ensure_ascii=False, indent=2))
    return 0


def project_status(project: Path) -> Dict[str, Any]:
    metadata = read_json(project / "project.json") if (project / "project.json").exists() else {}
    design_state = read_json(project / "design-run-state.json") if (project / "design-run-state.json").exists() else None
    review = read_json(project / "design-review.json") if (project / "design-review.json").exists() else None
    final_files = sorted(
        str(path.relative_to(project))
        for path in (project / "final").glob("*.pptx")
        if not path.name.startswith("~$")
    ) if (project / "final").exists() else []
    stage = metadata.get("stage", "delivered_clean" if final_files and not metadata else "outline")
    if design_state:
        stage = design_state.get("status", stage)
    editable_run = project / "editable-run"
    editable_validation_path = editable_run / "final" / "validation.json"
    if not editable_validation_path.exists():
        editable_validation_path = editable_run / "validation.json"
    editable_validation = read_json(editable_validation_path) if editable_validation_path.exists() else None
    finalized = (
        metadata.get("stage") == "finalized"
        and bool(final_files)
        and isinstance(editable_validation, dict)
        and editable_validation.get("passed") is True
    )
    if finalized:
        stage = "finalized"
    elif final_files and stage == "finalized":
        stage = "invalid_final_artifact"
    return {
        "project": str(project),
        "stage": stage,
        "outline_approved": bool(metadata.get("outline_approved")),
        "design_status": design_state.get("status") if design_state else None,
        "design_review": review.get("status") if review else None,
        "editable_validation": editable_validation.get("passed") if isinstance(editable_validation, dict) else None,
        "final_files": final_files,
    }


def command_status(args: argparse.Namespace) -> int:
    print(json.dumps(project_status(resolve_project(args.project)), ensure_ascii=False, indent=2))
    return 0


def run_python(script: str, *arguments: str) -> None:
    subprocess.run([sys.executable, str(SKILL_ROOT / "scripts" / script), *arguments], check=True)


def command_prepare_design(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    spec = read_json(project / "deck_spec.json")
    if spec.get("outline_approved") is not True:
        raise SystemExit("Outline approval is required before preparing design jobs")
    run_python("prepare_design_jobs.py", str(project), "--catalog", args.catalog)
    metadata_path = project / "project.json"
    metadata = read_json(metadata_path) if metadata_path.exists() else {"schema_version": 1}
    metadata["stage"] = "waiting_for_designs"
    metadata["outline_approved"] = True
    write_json(metadata_path, metadata)
    return 0


def command_review_designs(args: argparse.Namespace) -> int:
    run_python("review_designs.py", str(resolve_project(args.project)))
    return 0


def require_review_pass(project: Path) -> None:
    review = read_json(project / "design-review.json")
    if review.get("status") != "passed":
        raise SystemExit("Design review is not passed; editable reconstruction is blocked")


def command_prepare_editable(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    require_review_pass(project)
    sources = sorted((project / "design-drafts").glob("slide-*.png"))
    if not sources:
        raise SystemExit("No design drafts found")
    command = ["editppt", "prepare"] + [str(path) for path in sources] + [
        "--job-dir", str(project / "editable-run"),
        "--image-backend", "builtin-imagegen",
        "--no-text-hints",
    ]
    subprocess.run(command, check=True)
    metadata = read_json(project / "project.json")
    metadata["stage"] = "editable_prepared"
    write_json(project / "project.json", metadata)
    print("Editable page jobs prepared in %s" % (project / "editable-run"))
    return 0


def require_visual_fidelity_pass(project: Path) -> None:
    run_dir = project / "editable-run"
    jobs = read_json(run_dir / "page_jobs.json")
    failures = []
    for job in jobs.get("pages", []):
        page_id = str(job.get("page_id") or "unknown")
        page_dir_value = Path(str(job.get("page_dir") or ("pages/" + page_id)))
        page_dir = page_dir_value if page_dir_value.is_absolute() else run_dir / page_dir_value
        report_path = page_dir / "visual-fidelity.json"
        if not report_path.exists():
            failures.append("%s: missing visual-fidelity.json" % page_id)
            continue
        report = read_json(report_path)
        checks = report.get("checks") if isinstance(report, dict) else None
        if report.get("passed") is not True or not isinstance(checks, dict):
            failures.append("%s: visual fidelity did not pass" % page_id)
            continue
        failed_checks = [key for key in VISUAL_FIDELITY_CHECKS if checks.get(key) is not True]
        if failed_checks:
            failures.append("%s: failed checks %s" % (page_id, ", ".join(failed_checks)))
    if failures:
        raise SystemExit("Visual-fidelity gate blocked finalization:\n- " + "\n- ".join(failures))


def cleanup_project(project: Path, keep_deliverables: Optional[list[str]] = None) -> None:
    final_dir = project / "final"
    if final_dir.is_symlink() or not final_dir.is_dir():
        raise SystemExit("Cleanup refused: final must be a real project directory")
    metadata_path = project / "project.json"
    if not metadata_path.is_file() or read_json(metadata_path).get("stage") != "finalized":
        raise SystemExit("Cleanup refused: project is not finalized")
    keep = {
        path.name for path in final_dir.iterdir()
        if path.suffix.lower() == ".pptx" and not path.name.startswith("~$")
        and path.is_file() and not path.is_symlink()
    }
    if not keep:
        raise SystemExit("Cleanup refused: no final PPTX exists in %s" % final_dir)
    # Validate the entire whitelist before any mutation. Only concrete direct
    # files are accepted; directories, links and traversal cannot broaden scope.
    for name in keep_deliverables or []:
        path = final_dir / name
        if (Path(name).name != name or name in {".", ".."}
                or not path.is_file() or path.is_symlink()):
            raise SystemExit("Cleanup refused: keep-deliverable must name an existing file in final/: %s" % name)
        keep.add(name)

    def remove(path: Path) -> None:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()

    for child in list(final_dir.iterdir()):
        if child.name not in keep:
            remove(child)
    # These names belong to this workflow. Unknown inputs/shared directories
    # are not disposable merely because they sit beside generated workfiles.
    generated = set(PROJECT_DIRS) - {"final"}
    generated.update({
        "brief.md", "outline.md", "deck_spec.json", "template-map.json",
        "project.json", "design-jobs.json", "design-run-state.json",
        "design-review.json", "design-review-input.json",
    })
    for child in list(project.iterdir()):
        if child.name in generated:
            remove(child)


def command_finalize(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    if (project / "final").is_symlink():
        raise SystemExit("Finalization refused: final must not be a symlink")
    run_dir = project / "editable-run"
    require_visual_fidelity_pass(project)
    subprocess.run(["editppt", "run", "finalize", str(run_dir)], check=True)
    summary_path = run_dir / "final" / "run_summary.json"
    summary = read_json(summary_path) if summary_path.exists() else {}
    validation_value = summary.get("validation") or "final/validation.json"
    validation_path = Path(str(validation_value))
    if not validation_path.is_absolute():
        validation_path = run_dir / validation_path
    validation = read_json(validation_path)
    if validation.get("passed") is not True:
        raise SystemExit("editppt finalize did not produce a passing validation report")
    manifest = read_json(run_dir / "deck_manifest.json")
    output_value = summary.get("output") or manifest.get("output")
    if not output_value:
        raise SystemExit("editppt deck manifest does not declare the finalized output")
    source = Path(str(output_value))
    if not source.is_absolute():
        source = run_dir / source
    if not source.exists():
        raise SystemExit("editppt finalized output is missing: %s" % source)
    spec = read_json(project / "deck_spec.json")
    name = str(spec.get("deck_name") or project.name).strip().replace("/", "-")
    destination = project / "final" / (name + ".pptx")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    metadata = read_json(project / "project.json")
    metadata["stage"] = "finalized"
    write_json(project / "project.json", metadata)
    if not args.keep_workfiles:
        cleanup_project(project, args.keep_deliverable)
    print(destination)
    return 0


def command_cleanup(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    cleanup_project(project, args.keep_deliverable)
    print(project / "final")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    checks = []
    checks.append({"name": "template", "passed": DEFAULT_TEMPLATE.exists(), "path": str(DEFAULT_TEMPLATE)})
    catalog_ok = False
    catalog_count = None
    if DEFAULT_CATALOG.exists():
        catalog = read_json(DEFAULT_CATALOG)
        catalog_count = catalog.get("slide_count")
        catalog_ok = catalog_count == 42 and len(catalog.get("slides", [])) == 42
    checks.append({"name": "template_catalog", "passed": catalog_ok, "slide_count": catalog_count})
    editppt = shutil.which("editppt")
    editppt_ok = False
    if editppt:
        result = subprocess.run([editppt, "--help"], text=True, capture_output=True)
        editppt_ok = result.returncode == 0
    checks.append({"name": "editppt", "passed": editppt_ok, "path": editppt})
    # The orchestration scripts support the macOS system Python. The vendored
    # editppt runtime uses its own >=3.10 environment, verified by invoking the
    # installed CLI above.
    checks.append({"name": "orchestrator_python", "passed": sys.version_info >= (3, 9), "version": sys.version.split()[0]})
    payload = {"skill_root": str(SKILL_ROOT), "passed": all(item["passed"] for item in checks), "checks": checks}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["passed"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor").set_defaults(func=command_doctor)
    init = sub.add_parser("init")
    init.add_argument("--brief", required=True)
    init.add_argument("--out", required=True)
    init.set_defaults(func=command_init)
    prepare_design = sub.add_parser("prepare-design")
    prepare_design.add_argument("project")
    prepare_design.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    prepare_design.set_defaults(func=command_prepare_design)
    review = sub.add_parser("review-designs")
    review.add_argument("project")
    review.set_defaults(func=command_review_designs)
    editable = sub.add_parser("prepare-editable")
    editable.add_argument("project")
    editable.set_defaults(func=command_prepare_editable)
    finalize = sub.add_parser("finalize")
    finalize.add_argument("project")
    finalize.add_argument("--keep-workfiles", action="store_true", help="retain production workfiles only when explicitly requested")
    finalize.add_argument("--keep-deliverable", action="append", default=[], metavar="FILENAME", help="retain an explicitly requested file in final/; repeat for multiple files")
    finalize.set_defaults(func=command_finalize)
    cleanup = sub.add_parser("cleanup")
    cleanup.add_argument("project")
    cleanup.add_argument("--keep-deliverable", action="append", default=[], metavar="FILENAME", help="retain an explicitly requested file in final/; repeat for multiple files")
    cleanup.set_defaults(func=command_cleanup)
    status = sub.add_parser("status")
    status.add_argument("project")
    status.set_defaults(func=command_status)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
