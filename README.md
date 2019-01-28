# miscripts

- `commitdate`: reads and prints the "committed date" of a specified ref from a
  git repository, for use with RPM .spec files for snapshot builds
- `manifest_to_provides.py`: reads a go `manifest` file and converts it into a
  list of `Provides: bundled(foo)` for use in RPM .spec files
- `mdfmt.py`: reformats Markdown files for prettily aligned columns in tables
- `spec-glob-search.py`: searches RPM .spec files for lines matching a specific
  regular expression
- `spectool.py`: replacement for the `spectool` PERL script from `rpmdevtools`

