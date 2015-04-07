```bash
  sudo apt-get install pip
  sudo pip install virtualenv virtualenvwrapper
  source $(which virtualenvwrapper.sh)
  mkvirtualenv --no-site-packages registrelobbying
  workon registrelobbying
  pip install -r requirements.txt
  add2virtualenv .
  deactivate 
```
