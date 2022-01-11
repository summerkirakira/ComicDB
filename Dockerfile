FROM python:3.7-alpine
MAINTAINER hongpeizheng <zhenghongpei@gmail.com>
COPY . .
RUN python3 -m pip install -r requirements.txt
EXPOSE 8080
VOLUME '/data' '/database' '/log'
CMD ["sh", "run.sh"]

