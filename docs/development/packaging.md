# Packaging and deployment

## Packaging

This plugin is using the [qgis-plugin-ci](https://github.com/opengisch/qgis-plugin-ci/) tool to perform packaging operations.

```bash
qgis-plugin-ci release 0.3.1
```

## Release a version

### Using GitLab CI

1. Fillfull the `CHANGELOG.md`
2. Apply a git tag with the relevant version: `git tag -a 0.3.0 {git commit hash} -m "September 2019"`
3. Push tag to master
