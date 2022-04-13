# Packaging and deployment

## Packaging

This plugin is using the [qgis-plugin-ci](https://github.com/opengisch/qgis-plugin-ci/) tool to perform packaging operations.  
Under the hood, the package command is performing a `git archive` run based on `CHANGELOG.md`.

Install additional dependencies:

```bash
python -m pip install -U -r requirements/packaging.txt
```

Then use it:

```bash
# package a specific version
qgis-plugin-ci package 1.3.1
# package latest version
qgis-plugin-ci package latest
```

## Release a version

Everything is done through git workflow and GitLab CI/CD:

1. Add the new version to the `CHANGELOG.md`
1. Change the version number in `__about__.py`
1. Apply a git tag with the relevant version: `git tag -a 0.3.0 {git commit hash} -m "This version rocks!"`
1. Push tag to main branch: `git push origin 0.3.0`
