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
1. Optionally change the version number in `metadata.txt`
1. Apply a git tag with the relevant version: `git tag -a X.y.z {git commit hash} -m "This version rocks!"`
1. Push tag to main branch: `git push origin X.y.z`

:::{tip}
To get a prettified list of merged MR since a given tag, the following command can be helpful:

```sh
git log 1.4.1..HEAD --merges --pretty=format:"%s|%an|%b" | sed -nE 's/.*\|([^|]+)\|(.+)/- \2 by @\1/p'
```
:::
