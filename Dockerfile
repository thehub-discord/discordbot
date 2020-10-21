FROM python:3.8
COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN mkdir bot
WORKDIR bot/
COPY . ./
CMD ["python", "bot.py"]
