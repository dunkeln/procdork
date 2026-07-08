from __future__ import annotations

from pathlib import Path

from extraction import HarnessModel


class OkfAsset(HarnessModel):
    name: str
    kind: str
    resource: str
    okf_path: str


class OkfFlushResult(HarnessModel):
    assets: list[OkfAsset]


def flush_okf(
    marts_root: Path | str = "transforms/dbt/models/marts",
    okf_root: Path | str = "okf",
) -> OkfFlushResult:
    marts_path = Path(marts_root)
    okf_path = Path(okf_root)
    assets_dir = okf_path / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    assets = [write_mart_okf(path, assets_dir) for path in sorted(marts_path.glob("*.sql"))]
    write_index(okf_path / "README.md", assets)
    return OkfFlushResult(assets=assets)


def write_mart_okf(sql_path: Path, assets_dir: Path) -> OkfAsset:
    name = sql_path.stem
    okf_file = assets_dir / f"{name}.md"
    relative_resource = Path("..") / ".." / sql_path
    okf_file.write_text(mart_doc(name, relative_resource), encoding="utf-8")
    return OkfAsset(
        name=name,
        kind="dbt_model",
        resource=relative_resource.as_posix(),
        okf_path=okf_file.as_posix(),
    )


def write_index(path: Path, assets: list[OkfAsset]) -> None:
    lines = [
        "# Harness OKF",
        "",
        "Generated from promoted harness assets.",
        "",
        "Transient SQL observations stay in DuckDB. Raw captures stay in blob storage.",
        "",
        "## Assets",
        "",
    ]
    if assets:
        lines.extend(f"- [{asset.name}](assets/{asset.name}.md) - {asset.kind}" for asset in assets)
    else:
        lines.append("- No promoted assets yet.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mart_doc(name: str, resource: Path) -> str:
    return "\n".join(
        [
            "---",
            "okf_kind: dbt_model",
            f"name: {name}",
            "status: promoted",
            f"resource: {resource.as_posix()}",
            "---",
            "",
            f"# {name}",
            "",
            "This OKF concept describes a promoted dbt mart.",
            "",
            "The SQL file is the executable contract. This file is only the knowledge surface.",
            "",
        ]
    )
