FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Mode paper par défaut — aucune clé requise. Volumes : data/, state/, logs/.
CMD ["python", "scripts/run_paper.py"]
