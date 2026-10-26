FROM python:3.12-slim
WORKDIR /app
COPY growthpilot ./growthpilot
RUN useradd --uid 10001 --create-home pilot && mkdir /app/data && chown pilot:pilot /app/data
USER pilot
EXPOSE 8098
CMD ["python", "-m", "growthpilot.server", "--host", "0.0.0.0"]
