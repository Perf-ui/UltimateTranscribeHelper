"""Create a ZIP64 archive of an already tested Windows portable folder."""
from pathlib import Path
import sys
import zipfile


def main():
    root = Path(__file__).resolve().parents[2] / "dist"
    name = sys.argv[1] if len(sys.argv) > 1 else "Omnizart-Windows"
    if Path(name).name != name:
        raise SystemExit("Provide a folder name, not a path.")
    archive_name = sys.argv[2] if len(sys.argv) > 2 else name
    if Path(archive_name).name != archive_name:
        raise SystemExit("Provide an archive name, not a path.")
    source = root / name
    archive = root / (archive_name + ".zip")
    temporary = root / (archive_name + ".zip.partial")
    if not (source / "Omnizart.vbs").is_file():
        raise SystemExit("The portable folder is missing or incomplete.")
    if archive.exists() or temporary.exists():
        raise SystemExit("Rename the existing archive or partial archive first.")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=1, allowZip64=True) as output:
        for path in source.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                output.write(path, path.relative_to(root))
    temporary.replace(archive)
    print(f"Created {archive}")


if __name__ == "__main__":
    main()
