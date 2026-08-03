# 31/07
## Setup minikube e vulnerable-web-app pod
```bash
# Start the kubernetis cluster
minikube start --driver=docker --cpus=4 --memory=8192

cd src/webapp/

# Entra nell'ambiente docker dei minikube
eval $(minikube -p minikube docker-env)

# Build dell'immagine
docker build -t vulnerable-web-app:v1 .

# Applica Deployment + Service al cluster
kubectl apply -f app-deployment.yaml

# Verifica deploy
kubectl get pods -n demo-targets

# Test vulnerabilità
kubectl run attacker -n demo-targets --rm -i --tty --image=curlimages/curl -- sh
> curl "http://vulnerable-web-service/ping?host=127.0.0.1;cat%20/etc/passwd"
```

# 03/08
## Installazione helm
```bash
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4
chmod 700 get_helm.sh
./get_helm.sh
```
## Installazione Falco e primi test
```bash
# Aggiunta la repo helm
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# Installazione Falco
helm install --replace falco --namespace falco --create-namespace --set tty=true falcosecurity/falco
```
