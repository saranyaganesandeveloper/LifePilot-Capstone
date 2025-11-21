# -------- Stage 1: Build --------
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# -------- Stage 2: Production --------
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy entire project
COPY . .

# Streamlit Cloud Run settings
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "streamlit run src/ui/app.py --server.port=$PORT --server.address=0.0.0.0"]
