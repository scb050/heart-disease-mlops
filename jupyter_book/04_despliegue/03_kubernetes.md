# 4.3 Despliegue local con Kubernetes

Con la imagen Docker lista, el siguiente paso es desplegarla en un orquestador
que se haga cargo de mantenerla viva, escalarla y exponerla.  Usamos
**Kubernetes** en modo local (por ejemplo Minikube, Kind o Docker Desktop).

## Los dos manifiestos

El despliegue se describe con dos archivos YAML declarativos:

- [`k8s/deployment.yaml`](../../k8s/deployment.yaml) → cuántas réplicas correr
  y con qué imagen.
- [`k8s/service.yaml`](../../k8s/service.yaml) → cómo exponer esas réplicas al
  exterior.

## Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: heart-model
spec:
  replicas: 1
  selector:
    matchLabels:
      app: heart-model
  template:
    metadata:
      labels:
        app: heart-model
    spec:
      containers:
        - name: heart-model
          image: TU_USUARIO_DOCKER/heart-api:latest
          ports:
            - containerPort: 8000
```

### Qué hace cada campo

| Campo | Función |
|---|---|
| `kind: Deployment` | Tipo de recurso — gestiona pods y re-crea los que mueran. |
| `replicas: 1` | Una sola instancia. En producción se escalaría con HPA. |
| `selector.matchLabels` | Cómo el Deployment reconoce sus pods. |
| `template.metadata.labels` | Las etiquetas que llevan los pods creados. |
| `containers.image` | Imagen a correr — se debe subir antes a Docker Hub. |
| `containerPort: 8000` | Puerto que la API expone dentro del contenedor. |

```{admonition} Importante
:class: warning

Reemplaza `TU_USUARIO_DOCKER` por tu usuario real de Docker Hub (por ejemplo
`mateo/heart-api:latest`). Kubernetes **no puede usar imágenes locales** de tu
máquina a menos que uses el daemon interno (Minikube tiene `minikube image load`).
```

## Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: heart-service
spec:
  selector:
    app: heart-model
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

### Cómo funciona

- **`selector`** → le dice al Service a qué pods rutear el tráfico (los que
  tengan la etiqueta `app: heart-model`).
- **`port: 80`** → el puerto expuesto hacia el cliente.
- **`targetPort: 8000`** → el puerto interno del contenedor, donde escucha
  uvicorn.
- **`type: LoadBalancer`** → en la nube (GKE/EKS/AKS) pide una IP pública. En
  local, Minikube simula esto y expone la IP virtual.

## Flujo completo de despliegue

```bash
# 1. Build de la imagen
docker build -f docker/Dockerfile -t TU_USUARIO/heart-api:latest .

# 2. Push a Docker Hub
docker push TU_USUARIO/heart-api:latest

# 3. Aplicar los manifiestos
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 4. Verificar
kubectl get pods -l app=heart-model
kubectl get svc heart-service

# 5. Obtener URL
minikube service heart-service --url     # si usas Minikube
```

## Qué gana el proyecto al usar Kubernetes

| Capacidad | Cómo lo provee K8s |
|---|---|
| **Auto-recuperación** | Si un pod muere, el Deployment crea otro. |
| **Escalamiento horizontal** | `kubectl scale deployment heart-model --replicas=5`. |
| **Rolling updates** | Al cambiar la imagen, K8s reemplaza pods sin caída. |
| **Abstracción de red** | El Service da una IP y nombre DNS estables. |
| **Desacoplamiento** | El resto del sistema sólo conoce `heart-service`. |

```{admonition} Mejoras para producción
:class: note

El YAML actual es intencionalmente minimalista para efectos didácticos. En un
entorno real se agregaría:

- `resources.requests` y `resources.limits` (CPU y memoria).
- `livenessProbe` y `readinessProbe` apuntando a `/health`.
- `replicas >= 2` para alta disponibilidad.
- `HorizontalPodAutoscaler` basado en CPU.
- Secrets para variables sensibles.
- Ingress + TLS en vez de `LoadBalancer`.
```
