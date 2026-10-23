kubectl apply -f k8s-improved.yaml

kubectl get pods  

kubectl delete -f k8s-improved.yaml --ignore-not-found

python3 -c "from original_bully import bully_election; print(bully_election(2, [True, True, True, True, True, False]))"