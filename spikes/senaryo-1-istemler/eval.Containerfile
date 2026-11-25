FROM python:3.12-slim
RUN pip install --no-cache-dir itsdangerous==2.2.0 blinker==1.9.0 click==8.1.7 Flask==3.1.0 Jinja2==3.1.4 \
    MarkupSafe==3.0.2 Werkzeug==3.1.3 passlib==1.7.4 fpdf==1.7.2 pyjwt==2.10.1 pydantic==2.14.2
ENV PYTHONDONTWRITEBYTECODE=1
USER nobody
