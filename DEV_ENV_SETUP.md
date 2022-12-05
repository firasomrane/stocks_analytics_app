
## For development:
If using Mac
- Install pyenv to handle python versions
- Install `pyenv-mkvirtualenv` to create python virtual environments and isolate packages

```
brew install pyenv
brew install pyenv-virtualenvwrapper
```

- Add pyenv bin to the $PATH adding this to the entrypoint of the shell used, for example if using zsh then add this to the `.zshrc` file
```
# PYENV
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

- Install python 3.10 and use it as default version
```
pyenv install -l # list all available python versions
pyenv install 3.10.4 # If 3.10.4 is availabel
pyenv global 3.10.4
```
Now running `python --version` should return
```
Python 3.10.4
```

- Create new isolated python virtual environment
```
pyenv virtualenvwrapper
mkvirtualenv syrup_tech
workon syrup_tech
```

- Isntall Docker and docker-compose
- Install some useful python packages

    - [`pip-compile`](https://pypi.org/project/pip-tools/) to better manage python dependencies `pip3 install pip-tools`
    - [`pre-commit`](https://pre-commit.com/) for multi-language pre-commit hooks management `pip install pre-commit`
