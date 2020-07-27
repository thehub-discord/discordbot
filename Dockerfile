FROM python:3.8
RUN mkdir bot
WORKDIR bot/
COPY . ./
RUN pip install -r requirements.txt
CMD ["python", "bot.py"]