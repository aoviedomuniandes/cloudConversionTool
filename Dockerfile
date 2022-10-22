FROM python:3.10.2
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8081
# Declaramos una variable de entorno
ENV NAME apicoversiontool
# Ejecuta nuestra aplicación cuando se inicia el contenedor
CMD ["gunicorn", "app:create_app", "-c", "./gunicorn.conf.py"]