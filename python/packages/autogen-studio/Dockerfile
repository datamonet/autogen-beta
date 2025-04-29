FROM python:3.10-slim
WORKDIR /code

RUN pip install -U gunicorn autogenstudio e2b_code_interpreter
RUN pip install -U PyJWT psycopg2-binary 

ENV AUTOGENSTUDIO_APPDIR=/app

WORKDIR /app

COPY . /app

CMD gunicorn -w $((2 * $(getconf _NPROCESSORS_ONLN) + 1)) --timeout 12600 -k uvicorn.workers.UvicornWorker autogenstudio.web.app:app --bind "0.0.0.0:3003"
