# Deploying Multi-Tenant Backend on Kubernetes

Analysis of deploying the shared-app-dedicated-db architecture on Kubernetes, with comparison to Render.com deployment.

## Executive Summary

**Yes**, the shared-app-dedicated-db architecture is fully compatible with Kubernetes deployment. In fact, Kubernetes provides superior capabilities for this architecture compared to Render.com:

✅ **Dynamic database connections** - Supported via ConfigMaps/Secrets
✅ **Horizontal scaling** - HorizontalPodAutoscaler for traffic bursts
✅ **High availability** - Multi-replica deployments with load balancing
✅ **Rolling updates** - Zero-downtime deployments
✅ **Resource isolation** - CPU/memory limits per deployment
✅ **Secret management** - External Secrets Operator for tenant DB credentials

## Architecture Comparison

### Current Plan: Render.com

```
Render.com Blueprint (render.yaml)
├── Chat API (Docker container)
├── Admin API (Docker container)
├── Admin UI (Docker container)
└── PostgreSQL Database (managed)
```

**Characteristics**:
- Simple deployment (git push)
- Managed database
- Automatic HTTPS
- Limited scaling control
- Fixed resource allocation

### Code Sharing Strategy

**Important**: Both Chat API and Admin API use the **same Python codebase**. They are NOT separate applications.

**Option A: Environment Variable Router Selection** (Recommended for Kubernetes)
```python
# Single Docker image, different router exposure
# backend/app/main.py

app = FastAPI()

# Determine which routers to expose based on environment
exposed_routers = os.getenv('EXPOSED_ROUTERS', 'all').split(',')

if 'all' in exposed_routers or 'chat' in exposed_routers:
    app.include_router(account_agents.router)  # Chat endpoints
    app.include_router(chat_router)

if 'all' in exposed_routers or 'admin' in exposed_routers:
    app.include_router(admin_router)  # Admin endpoints
    app.include_router(directory_admin_router)

# Deployment with EXPOSED_ROUTERS=chat → Only chat endpoints
# Deployment with EXPOSED_ROUTERS=admin → Only admin endpoints
```

**Option B: Different Entry Points** (Current Render.com approach)
```
backend/               # Shared codebase
services/
  chat-api/
    main.py           # Exposes only chat routers
    Dockerfile        # Uses backend/ code
  admin-api/
    main.py           # Exposes only admin routers
    Dockerfile        # Uses backend/ code
```

**Verdict**: Option A is cleaner for Kubernetes (single image, environment-based configuration).

### Proposed: Kubernetes

```
Kubernetes Cluster
├── Namespace: salient-prod
│   ├── Deployment: chat-api (3 replicas)
│   │   └── Image: salient-backend:latest
│   │       └── EXPOSED_ROUTERS=chat
│   ├── Deployment: admin-api (2 replicas)
│   │   └── Image: salient-backend:latest  (SAME IMAGE!)
│   │       └── EXPOSED_ROUTERS=admin
│   ├── Deployment: admin-ui (2 replicas)
│   ├── Service: chat-api-svc (ClusterIP)
│   ├── Service: admin-api-svc (ClusterIP)
│   ├── Ingress: salient-ingress (HTTPS routing)
│   ├── HPA: chat-api-hpa (auto-scaling)
│   └── Secrets: tenant-db-credentials
│
├── Namespace: salient-admin
│   └── PostgreSQL (StatefulSet or External)
│       ├── Database: tenant_a
│       ├── Database: tenant_b
│       ├── Database: tenant_c
│       └── Database: salient_admin (tenant registry)
│
└── External Secrets Operator
    └── SecretStore: tenant-db-store
```

**Characteristics**:
- Declarative infrastructure (YAML)
- Auto-scaling (HPA)
- Self-healing (pod restarts)
- Rolling updates
- Resource efficiency
- **Single codebase, multiple deployments**
- More operational complexity

## FastAPI Router Selection Pattern

### Implementation in main.py

```python
# backend/app/main.py
import os
from fastapi import FastAPI
from .api import account_agents, admin, directory_admin
import logfire

app = FastAPI(title="Salient API")

# Determine which routers to expose based on environment variable
exposed_routers = os.getenv('EXPOSED_ROUTERS', 'all').split(',')

logfire.info(
    'app.router_configuration',
    exposed_routers=exposed_routers,
    mode='kubernetes' if 'all' not in exposed_routers else 'development'
)

# Chat/Public endpoints
if 'all' in exposed_routers or 'chat' in exposed_routers:
    app.include_router(
        account_agents.router,
        tags=["chat", "multi-tenant"]
    )
    logfire.info('app.router_included', router='account_agents')

# Admin endpoints (JWT protected)
if 'all' in exposed_routers or 'admin' in exposed_routers:
    app.include_router(
        admin.router,
        prefix="/api/admin",
        tags=["admin"]
    )
    app.include_router(
        directory_admin.router,
        prefix="/api/admin",
        tags=["admin", "directory"]
    )
    logfire.info('app.router_included', router='admin')

# Health check (always included)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "routers": exposed_routers}
```

### How It Works

**Chat API Pods** (`EXPOSED_ROUTERS=chat`):
```
Available endpoints:
  POST   /accounts/{account_slug}/agents/{instance_slug}/chat
  GET    /accounts/{account_slug}/agents/{instance_slug}/stream
  GET    /accounts/{account_slug}/agents
  GET    /health

NOT available:
  /api/admin/*  (not included)
```

**Admin API Pods** (`EXPOSED_ROUTERS=admin`):
```
Available endpoints:
  POST   /api/admin/accounts/{account_id}/tokens
  GET    /api/admin/accounts/{account_id}/tokens
  DELETE /api/admin/accounts/{account_id}/tokens/{token_id}
  GET    /api/admin/directory-schemas
  GET    /health

NOT available:
  /accounts/*  (not included)
```

**Local Development** (`EXPOSED_ROUTERS=all` or not set):
```
All endpoints available (default behavior)
```

### Benefits of Single Codebase Approach

**1. Code Reuse**:
- ✅ Shared models, services, middleware
- ✅ No code duplication
- ✅ Single dependency management

**2. Simplified Deployment**:
- ✅ One Docker image to build
- ✅ One image to scan for vulnerabilities
- ✅ Faster CI/CD pipeline

**3. Version Consistency**:
- ✅ Both deployments use same code version
- ✅ No version drift between services
- ✅ Easier rollback (same image)

**4. Scaling Flexibility**:
- ✅ Scale chat and admin independently
- ✅ Different replica counts
- ✅ Different resource limits
- ✅ Different HPA policies

**5. Security Isolation**:
- ✅ Chat API exposed publicly (via Ingress)
- ✅ Admin API can be internal-only
- ✅ Network policies can restrict admin access
- ✅ Different authentication requirements

### Network Isolation Example

```yaml
# k8s/network-policy-admin.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: admin-api-policy
  namespace: salient-prod
spec:
  podSelector:
    matchLabels:
      component: admin-api
  policyTypes:
  - Ingress
  ingress:
  # Only allow traffic from specific IP ranges (VPN, office)
  - from:
    - ipBlock:
        cidr: 10.0.0.0/8  # Internal network only
    ports:
    - protocol: TCP
      port: 8000
```

This ensures admin API is **never accessible from public internet**, even though it uses the same codebase as chat API.

## Kubernetes Deployment Manifests

### 1. Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: salient-prod
  labels:
    app: salient
    env: production
```

### 2. ConfigMap (Application Config)

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: salient-config
  namespace: salient-prod
data:
  POSTGRES_ADMIN_URL: "postgresql://postgres:5432/salient_admin"
  POSTGRES_HOST: "postgres.salient-admin.svc.cluster.local"
  POSTGRES_PORT: "5432"
  LOG_LEVEL: "info"
  ENVIRONMENT: "production"
```

### 3. Secrets (Tenant Database Credentials)

**Option A: Manual Secrets (Simple)**

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: tenant-db-credentials
  namespace: salient-prod
type: Opaque
stringData:
  POSTGRES_ADMIN_USER: "postgres"
  POSTGRES_ADMIN_PASSWORD: "admin_password_here"
  # Individual tenant DB credentials can be stored in admin database
  # and fetched at runtime by TenantEngineManager
```

**Option B: External Secrets Operator (Recommended)**

```yaml
# k8s/external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: tenant-db-store
  namespace: salient-prod
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: salient-sa

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: tenant-db-external-secret
  namespace: salient-prod
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: tenant-db-store
    kind: SecretStore
  target:
    name: tenant-db-credentials
    creationPolicy: Owner
  data:
    - secretKey: POSTGRES_ADMIN_PASSWORD
      remoteRef:
        key: salient/postgres/admin-password
```

### 4. Deployment: Chat API

```yaml
# k8s/deployment-chat-api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chat-api
  namespace: salient-prod
  labels:
    app: salient
    component: chat-api
spec:
  replicas: 3  # High availability
  selector:
    matchLabels:
      app: salient
      component: chat-api
  template:
    metadata:
      labels:
        app: salient
        component: chat-api
    spec:
      containers:
      - name: chat-api
        image: ghcr.io/yourorg/salient-backend:latest  # SAME IMAGE
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        
        # Environment variables
        env:
        # THIS IS THE KEY: Expose only chat routers
        - name: EXPOSED_ROUTERS
          value: "chat"  # Only includes chat endpoints
        
        - name: POSTGRES_HOST
          valueFrom:
            configMapKeyRef:
              name: salient-config
              key: POSTGRES_HOST
        - name: POSTGRES_PORT
          valueFrom:
            configMapKeyRef:
              name: salient-config
              key: POSTGRES_PORT
        - name: POSTGRES_ADMIN_URL
          valueFrom:
            configMapKeyRef:
              name: salient-config
              key: POSTGRES_ADMIN_URL
        - name: POSTGRES_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: tenant-db-credentials
              key: POSTGRES_ADMIN_PASSWORD
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: tenant-db-credentials
              key: OPENROUTER_API_KEY
        - name: LOG_LEVEL
          value: "info"
        
        # Resource limits (important for HPA)
        resources:
          requests:
            cpu: 200m      # 0.2 CPU cores
            memory: 256Mi  # 256 MB
          limits:
            cpu: 500m      # 0.5 CPU cores max
            memory: 512Mi  # 512 MB max
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        
        # Graceful shutdown
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 10"]
      
      # Pod-level settings
      terminationGracePeriodSeconds: 30
      restartPolicy: Always
```

### 5. Deployment: Admin API

```yaml
# k8s/deployment-admin-api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: admin-api
  namespace: salient-prod
  labels:
    app: salient
    component: admin-api
spec:
  replicas: 2  # Lower traffic than chat API
  selector:
    matchLabels:
      app: salient
      component: admin-api
  template:
    metadata:
      labels:
        app: salient
        component: admin-api
    spec:
      containers:
      - name: admin-api
        image: ghcr.io/yourorg/salient-backend:latest  # SAME IMAGE as chat-api
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        
        env:
        # THIS IS THE KEY: Expose only admin routers
        - name: EXPOSED_ROUTERS
          value: "admin"  # Only includes admin endpoints
        
        - name: POSTGRES_ADMIN_URL
          valueFrom:
            configMapKeyRef:
              name: salient-config
              key: POSTGRES_ADMIN_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: tenant-db-credentials
              key: JWT_SECRET
        - name: JWT_ALGORITHM
          value: "HS256"
        
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 300m
            memory: 512Mi
        
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### 6. Service (ClusterIP)

```yaml
# k8s/service-chat-api.yaml
apiVersion: v1
kind: Service
metadata:
  name: chat-api-svc
  namespace: salient-prod
  labels:
    app: salient
    component: chat-api
spec:
  type: ClusterIP  # Internal only, accessed via Ingress
  selector:
    app: salient
    component: chat-api
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  sessionAffinity: None  # Stateless application

---
apiVersion: v1
kind: Service
metadata:
  name: admin-api-svc
  namespace: salient-prod
spec:
  type: ClusterIP
  selector:
    app: salient
    component: admin-api
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
```

### 7. Ingress (HTTPS Routing)

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: salient-ingress
  namespace: salient-prod
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.salient.ai
    - admin.salient.ai
    secretName: salient-tls-cert
  
  rules:
  # Chat API
  - host: api.salient.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: chat-api-svc
            port:
              number: 80
  
  # Admin API
  - host: admin.salient.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: admin-api-svc
            port:
              number: 80
```

### 8. HorizontalPodAutoscaler

```yaml
# k8s/hpa-chat-api.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: chat-api-hpa
  namespace: salient-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chat-api
  
  minReplicas: 3    # Always at least 3 for HA
  maxReplicas: 20   # Scale up to 20 pods under load
  
  metrics:
  # CPU-based scaling
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70  # Target 70% CPU utilization
  
  # Memory-based scaling
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80  # Target 80% memory utilization
  
  # Scaling behavior
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30  # Fast scale-up
      policies:
      - type: Percent
        value: 50        # Scale up by 50% of current pods
        periodSeconds: 60
      - type: Pods
        value: 2         # Or add 2 pods
        periodSeconds: 60
      selectPolicy: Max  # Use the larger of the two
    
    scaleDown:
      stabilizationWindowSeconds: 300  # Slow scale-down (5 min)
      policies:
      - type: Percent
        value: 10        # Scale down by 10% max
        periodSeconds: 60
      selectPolicy: Min
```

## Multi-Tenant Database Integration

### How Tenant Databases Work in Kubernetes

**1. TenantEngineManager Initialization**

```python
# Application startup (main.py)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize admin database connection
    admin_db_url = os.getenv('POSTGRES_ADMIN_URL')
    
    tenant_manager = get_tenant_engine_manager()
    await tenant_manager.initialize_admin_engine(admin_db_url)
    
    logfire.info('kubernetes.tenant_manager_initialized')
    
    yield
    
    # Shutdown
    await tenant_manager.shutdown()
```

**2. Runtime Tenant Database Access**

Each request triggers:
1. `TenantResolutionMiddleware` extracts tenant from URL/header/token
2. `get_tenant_db_session` dependency fetches tenant's engine
3. `TenantEngineManager` loads connection string from admin database
4. Creates/caches engine for tenant database
5. Returns session connected to tenant's dedicated database

**Connection String Storage**:
```sql
-- In salient_admin database (admin database)
SELECT 
  tenant_id,
  database_name,
  connection_string  -- postgresql://postgres:5432/tenant_a
FROM tenant_registry
WHERE tenant_id = 'abc-123' AND is_active = true;
```

### Dynamic Engine Creation Flow

```
Request → Middleware → Dependency → TenantEngineManager
                                         ↓
                            Check cache: tenant_id in _engines?
                                         ↓
                               YES ← Return cached engine
                                         ↓ NO
                            Query admin DB for tenant config
                                         ↓
                        create_async_engine(tenant_connection_string)
                                         ↓
                            Cache engine in _engines[tenant_id]
                                         ↓
                              Return new engine
```

### Connection Pooling Behavior

**Per-Pod Connection Pools**:
- Each pod has its own `TenantEngineManager` instance
- Each tenant gets a dedicated engine with its own pool
- Default: `pool_size=10, max_overflow=5` per tenant per pod

**Example with 3 pods and 5 tenants**:
```
Pod 1:
  - tenant_a: 10 connections (pool) + 5 overflow = 15 max
  - tenant_b: 10 connections + 5 overflow = 15 max
  - tenant_c: 10 connections + 5 overflow = 15 max
  - tenant_d: 10 connections + 5 overflow = 15 max
  - tenant_e: 10 connections + 5 overflow = 15 max
  = 75 max connections from Pod 1

Pod 2: 75 max connections
Pod 3: 75 max connections

Total potential: 225 connections to PostgreSQL
```

**Mitigations**:
1. **PgBouncer** - Connection pooler between app and PostgreSQL
2. **Smaller pool sizes** - `pool_size=5, max_overflow=2` for many tenants
3. **Lazy engine creation** - Only create engines when tenants are accessed
4. **Engine disposal** - Drop inactive tenant engines after timeout

### PgBouncer in Kubernetes

```yaml
# k8s/pgbouncer-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
  namespace: salient-admin
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pgbouncer
  template:
    metadata:
      labels:
        app: pgbouncer
    spec:
      containers:
      - name: pgbouncer
        image: pgbouncer/pgbouncer:latest
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: pgbouncer-config
          mountPath: /etc/pgbouncer
        env:
        - name: DATABASES_HOST
          value: postgres.salient-admin.svc.cluster.local
      volumes:
      - name: pgbouncer-config
        configMap:
          name: pgbouncer-config

---
apiVersion: v1
kind: Service
metadata:
  name: pgbouncer-svc
  namespace: salient-admin
spec:
  type: ClusterIP
  selector:
    app: pgbouncer
  ports:
  - port: 5432
    targetPort: 5432
```

**Application connects to PgBouncer instead of PostgreSQL**:
```python
# Connection strings point to PgBouncer
connection_string = "postgresql://pgbouncer-svc.salient-admin.svc.cluster.local:5432/tenant_a"
```

## Deployment Workflow

### 1. Build Single Container Image

**Key Point**: Build ONE Docker image that contains all the backend code.

```dockerfile
# Dockerfile (at repository root)
FROM python:3.14-slim

WORKDIR /app

# Copy entire backend
COPY backend/ /app/backend/
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Entry point uses environment variable to determine which routers to expose
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build single image
docker build -t ghcr.io/yourorg/salient-backend:v1.2.3 .
docker push ghcr.io/yourorg/salient-backend:v1.2.3

# This ONE image is used by BOTH chat-api and admin-api deployments
# The only difference is the EXPOSED_ROUTERS environment variable
```

### 2. Apply Kubernetes Manifests

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply secrets and config
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

# Deploy applications
kubectl apply -f k8s/deployment-chat-api.yaml
kubectl apply -f k8s/deployment-admin-api.yaml

# Create services
kubectl apply -f k8s/service-chat-api.yaml
kubectl apply -f k8s/service-admin-api.yaml

# Setup ingress
kubectl apply -f k8s/ingress.yaml

# Enable auto-scaling
kubectl apply -f k8s/hpa-chat-api.yaml
```

### 3. Verify Deployment

```bash
# Check pod status
kubectl get pods -n salient-prod

# Check HPA status
kubectl get hpa -n salient-prod

# Check logs
kubectl logs -f deployment/chat-api -n salient-prod

# Check ingress
kubectl get ingress -n salient-prod
```

### 4. Rolling Update (Zero Downtime)

```bash
# Update image version
kubectl set image deployment/chat-api \
  chat-api=ghcr.io/yourorg/salient-chat-api:v1.2.4 \
  -n salient-prod

# Watch rollout
kubectl rollout status deployment/chat-api -n salient-prod

# Rollback if needed
kubectl rollout undo deployment/chat-api -n salient-prod
```

## Cost Comparison

### Render.com (Current Plan)

```
Chat API: $25/month (Starter)
Admin API: $25/month (Starter)
Admin UI: $25/month (Starter)
PostgreSQL: $25/month (Starter)
Total: ~$100/month
```

**Limitations**:
- Fixed resources (512MB RAM, 0.5 CPU)
- No auto-scaling
- Limited to 1 instance per service

### Kubernetes (Managed - GKE/EKS/AKS)

**Small Cluster (Development)**:
```
3 nodes (e2-small): $25/node = $75/month
Load Balancer: $20/month
External PostgreSQL (Cloud SQL): $50/month
Total: ~$145/month
```

**Medium Cluster (Production)**:
```
5 nodes (e2-standard-2): $50/node = $250/month
Load Balancer: $20/month
External PostgreSQL (Cloud SQL): $100/month
Total: ~$370/month
```

**Benefits**:
- Auto-scaling (3-20 pods)
- High availability (multi-zone)
- Better performance
- Flexible resource allocation

### Kubernetes (Self-Managed)

```
3 VPS nodes (8GB RAM, 4 CPU): $40/node = $120/month
External PostgreSQL: $50/month
Total: ~$170/month
```

**Trade-off**: Lower cost but higher operational burden.

## When to Choose Kubernetes

**Choose Kubernetes if**:
✅ Need auto-scaling (traffic spikes)
✅ High availability is critical
✅ Multiple environments (dev/staging/prod)
✅ Team has Kubernetes expertise
✅ Growing to 10+ tenants with varying load
✅ Need resource efficiency (pack workloads)

**Stick with Render.com if**:
✅ Team is small (<5 engineers)
✅ Simple deployment is priority
✅ Don't need auto-scaling
✅ <10 tenants with predictable load
✅ Want managed everything (low ops burden)

## Hybrid Approach

**Phase 1**: Deploy on Render.com (MVP, validate product)
**Phase 2**: Move to managed Kubernetes (scale, HA requirements)
**Phase 3**: Optimize (self-managed, multi-region, edge deployment)

## Migration Path: Render.com → Kubernetes

### Step 1: Containerize Applications

✅ Already done - Dockerfiles exist in `services/` directories

### Step 2: Set Up Kubernetes Cluster

```bash
# Create GKE cluster (example)
gcloud container clusters create salient-prod \
  --num-nodes=3 \
  --machine-type=e2-standard-2 \
  --region=us-central1 \
  --enable-autoscaling \
  --min-nodes=3 \
  --max-nodes=10
```

### Step 3: Deploy PostgreSQL

**Option A**: Managed (Cloud SQL, RDS, Azure Database)
**Option B**: StatefulSet in Kubernetes (more complex)

### Step 4: Deploy Applications

Apply Kubernetes manifests (see above).

### Step 5: Configure DNS

Point `api.salient.ai` to Kubernetes Ingress IP.

### Step 6: Test & Validate

Run smoke tests, load tests, verify tenant isolation.

### Step 7: Cutover

Update DNS, monitor, rollback to Render.com if issues.

## Summary

**Verdict**: The shared-app-dedicated-db architecture is **fully compatible** with Kubernetes and provides significant benefits over Render.com for production workloads.

**Key Advantages**:
- ✅ Auto-scaling with HPA
- ✅ High availability (multi-replica)
- ✅ Resource efficiency
- ✅ Rolling updates (zero downtime)
- ✅ Better control over infrastructure

**Implementation Requirements**:
- Docker images for each service
- Kubernetes manifests (Deployment, Service, Ingress, HPA)
- External Secrets Operator for credential management
- Monitoring and observability setup
- Team with Kubernetes expertise

**Recommendation**: Start with Render.com for MVP, migrate to Kubernetes when scaling requirements justify the operational complexity.
