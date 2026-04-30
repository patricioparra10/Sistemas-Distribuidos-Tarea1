FROM python:3.11-slim
RUN pip install flask redis requests
COPY cache_service.py .
CMD ["python", "cache_service.py"]