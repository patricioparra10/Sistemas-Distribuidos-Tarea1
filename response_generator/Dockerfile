FROM python:3.11-slim
RUN pip install flask pandas numpy requests
COPY response_generator.py .
CMD ["python", "response_generator.py"]