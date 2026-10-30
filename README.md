## BYG FRA BUNDEN ALLE KOMMANDOER BRUGT

kubectl create namespace bully-original
kubectl create namespace bully-improved

kubectl get namespaces

docker build -t bully-original:latest -f Dockerfile .
docker build -t bully-improved:latest -f Dockerfile.improved .

kubectl apply -f k8s-original.yaml -n bully-original
kubectl apply -f k8s-improved.yaml -n bully-improved

kubectl get pods -n bully-original
kubectl get pods -n bully-improved

kubectl get services -n bully-original
kubectl get services -n bully-improved

kubectl logs p2 -n bully-original
kubectl logs p2 -n bully-improved

kubectl exec -n bully-original p6 -- python3 -c "import socket; s=socket.socket(); s.connect(('p6',5006)); s.sendall(b'ELECTION 5'); s.close()"

kubectl exec -n bully-improved p5 -- python3 -c "import socket; s=socket.socket(); s.connect(('p6',5006)); s.sendall(b'BECOME_LEADER 5'); s.close()"

kubectl delete pod p6 -n bully-original
kubectl delete pod p6 -n bully-improved

kubectl logs p5 -n bully-original
kubectl logs p5 -n bully-improved


## RESET

kubectl delete -f k8s-original.yaml -n bully-original
kubectl delete -f k8s-improved.yaml -n bully-improved

kubectl apply -f k8s-original.yaml -n bully-original
kubectl apply -f k8s-improved.yaml -n bully-improved

## KØR TESTFIL

python3 test_algorithms.py