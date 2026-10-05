FROM python:3.12-slim

WORKDIR /app

# Installer Flask og requests til den distribuerede Kubernetes-node
RUN pip install --no-cache-dir flask requests

# Kopier dine eksisterende filer + den distribuerede node-fil
COPY Bully_Alg.py Bully_Alg_Tests.py node.py ./

EXPOSE 5000

# Standard-kommando når containeren kører som Pod i Kubernetes StatefulSet
CMD ["python", "node.py"]
