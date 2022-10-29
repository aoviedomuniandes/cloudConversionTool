
### Install codec FFmpeg

Download FFmpeg https://ffmpeg.org/download.html
windows download: inscrutcciones para instalar sobre windows https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/


### Create a Python Virtual Environment

Create a Python 3.x virtual environment with:

    python -m venv venv

Depending on how Python has been installed, you might need to use "`python3`" on some systems (i.e. MacOS with Homebrew).

### Activate the Virtual Environment

Windows:

    .\venv\Scripts\activate

Linux/MacOS:

    .venv/bin/activate

### install requirements into enviorement
``` bash
   pip install -r requirements.txt
```

## start redis backend (using docker)
``` bash
docker run -d --name redis -p 6379:6379 redis
```
## run celery worker
``` bash
source .env
celery -A worker:celery worker --loglevel=DEBUG --pool=solo
```

## run flask app
``` bash
source .env
# check the available routes
flask routes
# start flask development server
flask run
```

## star docker compose build
``` bash
 docker-compose  up -d --build  
```
# down image compose docker
``` bash
 docker-compose  up -d --build  
```




