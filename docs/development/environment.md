# Development

## Environment setup

> Typical commands on Ubuntu, but work on Windows or other main Linux distributions.

### 1. Install virtual environment

Using [qgis-venv-creator](https://github.com/GispoCoding/qgis-venv-creator) (see [this article](https://blog.geotribu.net/2024/11/25/creating-a-python-virtual-environment-for-pyqgis-development-with-vs-code-on-windows/#with-the-qgis-venv-creator-utility) or [the original version in French](https://geotribu.fr/articles/2024/2024-11-25_pyqgis_environnement_dev_windows/)) through [pipx](https://pipx.pypa.io) (`sudo apt install pipx`):

```sh
pipx run qgis-venv-creator
```

Old school way:

```sh
# create virtual environment linking to system packages (for pyqgis)
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
```

### 2. Install development dependencies

```sh
# bump dependencies inside venv
python -m pip install -U pip
python -m pip install -U -r requirements/development.txt

# install git hooks (pre-commit)
pre-commit install
```

### 3. Create a dedicated QGIS profile

It's recommended to create a dedicated QGIS profile for the development of the plugin to avoid conflicts with other plugins.

1. From the command-line (a terminal with or OSGeo4W Shell):

    ```sh
    # Linux
    qgis --profile plg_french_locator
    # Windows - OSGeo4W Shell
    qgis-ltr --profile plg_french_locator
    # Windows - PowerShell opened in the QGIS installation directory
    PS C:\Program Files\QGIS 3.44.12\LTR\bin> .\qgis-ltr-bin.exe --profile plg_french_locator
    ```

1. Then, set the `QGIS_PLUGINPATH` environment variable to the path of the plugin in profile preferences:

    ![QGIS - Add QGIS_PLUGINPATH environment variable in profile settings](../_static/images/dev_qgis_set_pluginpath_envvar.png)

1. Finally, enable the plugin in the plugin manager (ignore invalid folders like documentation, tests, etc.):

    ![QGIS - Enable the plugin in the plugin manager](../_static/images/dev_qgis_enable_plugin.png)

## Resources

Interesting QGIS API documentation pages:

- <http://api.qgis.org/api/master/html/classQgisInterface.html>
- Geocoding with PyQGIS: <https://qgis.org/pyqgis/3.40/core/#geocoding>
- Locator bar: <https://qgis.org/pyqgis/3.40/core/#core-locator>
