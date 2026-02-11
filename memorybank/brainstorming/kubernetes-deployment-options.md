# Kubernetes Deployment Options for Multi-Tenant Backend

Clean-slate analysis of deployment options including Kubernetes providers and PaaS alternatives.

## Deployment Models Overview

### A. Platform-as-a-Service (PaaS)

Fully managed platform handling infrastructure, scaling, and operations.

**Providers**: Render.com, Heroku, Railway, Fly.io

**Pros**:
- Simplest deployment (git push)
- Automatic scaling and zero-downtime deploys
- Managed databases included
- SSL/TLS automatic
- No infrastructure management
- Fast time to market

**Cons**:
- Higher cost per resource (3-5x markup over raw compute)
- Less control over infrastructure
- Limited customization
- Potential vendor lock-in
- May not support all advanced features

**Best For**: Small teams, MVP stage, teams without DevOps expertise

### B. Managed Kubernetes (Cloud Provider)

Cloud provider manages control plane, you manage workloads.

**Providers**: AWS EKS, Google GKE, Azure AKS, DigitalOcean DOKS, Linode LKE, Vultr VKE

**Pros**:
- Control plane managed (upgrades, security patches)
- Integrated monitoring and logging
- Load balancer and ingress support
- Auto-scaling capabilities
- High availability built-in
- Integration with cloud ecosystem (storage, databases, secrets)

**Cons**:
- Higher cost than self-managed
- Vendor lock-in (cloud-specific features)
- Limited control plane customization
- Egress data transfer costs

### 2. Self-Managed Kubernetes

You manage both control plane and workloads on VPS/bare metal.

**Tools**: kubeadm, kops, Kubespray

**Pros**:
- Full control over infrastructure
- Lower compute costs
- No vendor lock-in
- Custom networking and storage

**Cons**:
- High operational burden (upgrades, monitoring, backups)
- Requires deep Kubernetes expertise
- Must manage high availability manually
- Security patching responsibility
- Time-intensive maintenance

### 3. Kubernetes-as-a-Service (Simplified)

Simplified Kubernetes with opinionated defaults.

**Providers**: Platform.sh, Railway, Porter

**Pros**:
- Easiest to use
- Good for teams without K8s expertise
- Faster time to deployment

**Cons**:
- Limited customization
- Vendor lock-in
- Often more expensive per resource
- May not support all K8s features

## Cloud Provider Comparison

### AWS EKS (Elastic Kubernetes Service)

**Control Plane**: $72/month ($0.10/hour)
**Worker Nodes**: EC2 pricing (varies)
**PostgreSQL**: RDS pricing starts ~$15/month (db.t3.micro), ~$150/month (db.t3.medium production)

**Pricing Example (Small Production)**:
```
Control Plane: $72/month
3 × t3.medium nodes: $30 × 3 = $90/month
RDS PostgreSQL (db.t3.medium): $150/month
Load Balancer: $18/month
EBS Storage (100GB): $10/month
Total: ~$340/month
```

**Pros**:
- Deepest integration with AWS ecosystem (IAM, VPC, CloudWatch)
- Best for organizations already on AWS
- Extensive feature set (Fargate, ECS integration)
- Strong enterprise support

**Cons**:
- Most expensive control plane ($72/month)
- Complex networking setup (VPC, subnets, NAT gateways)
- Steep learning curve
- Data egress charges can be high
- Many services require additional configuration

**Best For**: Organizations already invested in AWS, enterprise workloads, need for AWS-specific integrations.

### Google GKE (Google Kubernetes Engine)

**Control Plane**: Included in cluster cost (Autopilot) or free (Standard with 1 cluster)
**Worker Nodes**: Compute Engine pricing
**PostgreSQL**: Cloud SQL starts ~$10/month (db-f1-micro), ~$100/month (production)

**Pricing Example (Small Production)**:
```
Control Plane: $0 (first cluster free)
3 × e2-standard-2 nodes: $48 × 3 = $144/month
Cloud SQL PostgreSQL (db-n1-standard-1): $100/month
Load Balancer: $18/month
Persistent Disk (100GB): $17/month
Total: ~$279/month
```

**Pros**:
- Google created Kubernetes (most mature implementation)
- Autopilot mode (fully managed nodes)
- Excellent monitoring (Cloud Operations suite)
- Competitive networking costs
- Free control plane for first cluster
- Strong integration with Google Cloud services

**Cons**:
- Less familiar for non-Google Cloud users
- Smaller ecosystem than AWS
- Regional availability limitations
- Some features require specific machine types

**Best For**: Teams wanting the most Kubernetes-native experience, organizations using Google Cloud, teams valuing automation (Autopilot).

### Azure AKS (Azure Kubernetes Service)

**Control Plane**: Free
**Worker Nodes**: Azure VM pricing
**PostgreSQL**: Azure Database for PostgreSQL starts ~$25/month (Burstable), ~$120/month (production)

**Pricing Example (Small Production)**:
```
Control Plane: $0 (free)
3 × Standard_B2s nodes: $30 × 3 = $90/month
Azure PostgreSQL (General Purpose): $120/month
Load Balancer: $20/month
Managed Disk (100GB): $10/month
Total: ~$240/month
```

**Pros**:
- Free control plane (lowest fixed cost)
- Strong integration with Azure services (Active Directory, Key Vault)
- Good for organizations with Microsoft/Azure investments
- Virtual node serverless support
- Azure Policy for compliance

**Cons**:
- Less mature than GKE
- Historically slower feature adoption
- Some quirks in networking model
- Smaller community than AWS/GCP

**Best For**: Organizations using Azure/Microsoft stack, need for Azure AD integration, cost-conscious deployments.

### DigitalOcean Kubernetes (DOKS)

**Control Plane**: Free
**Worker Nodes**: Droplet pricing starting at $12/month
**PostgreSQL**: Managed Database starts at $15/month (1GB RAM), $30/month (2GB HA)

**Pricing Example (Small Production)**:
```
Control Plane: $0 (free)
3 × Basic Droplets (2GB/2vCPU): $18 × 3 = $54/month
Managed PostgreSQL (HA, 2GB): $30/month
Load Balancer: $12/month
Block Storage (100GB): $10/month
Total: ~$106/month
```

**Pricing Example (Medium Production)**:
```
Control Plane: $0 (free)
3 × General Purpose (4GB/2vCPU): $42 × 3 = $126/month
Managed PostgreSQL (HA, 4GB): $55/month
Load Balancer: $12/month
Block Storage (200GB): $20/month
Total: ~$213/month
```

**Pros**:
- Lowest total cost for small deployments
- Free control plane
- Simple, predictable pricing
- Easy to use (1-click setup)
- Good documentation
- Fast provisioning
- Included monitoring and backups
- Developer-friendly

**Cons**:
- Smaller feature set than big three
- Fewer regions (15 vs 25+ for AWS/GCP)
- Limited enterprise features
- Smaller ecosystem
- Less mature for very large scale (max 512 nodes)

**Best For**: Startups, small to medium businesses, cost-conscious teams, teams without deep K8s expertise, MVP to growth stage.

## Render.com (PaaS Alternative)

### Overview

Render.com is a modern PaaS that abstracts Kubernetes complexity, providing Docker deployment without managing infrastructure.

**Pricing**: $19-29/month per user + compute resources
**Control Plane**: Managed (abstracted away)
**PostgreSQL**: Managed database from $15/month
**Docker Support**: Full support with Dockerfiles or pre-built images

### Pricing Example (Small Production)

```
Chat API (Starter): $25/month (512MB RAM, 0.5 CPU)
Admin API (Starter): $25/month (512MB RAM, 0.5 CPU)
Admin UI (Starter): $25/month (512MB RAM, 0.5 CPU)
PostgreSQL (Starter): $25/month (1GB RAM)
Total: ~$100/month

OR with Professional plan:
Professional Plan: $19/user/month × 3 users = $57/month
Compute resources: Same as above ($75/month)
Total: ~$132/month
```

### Pricing Example (Medium Production)

```
Chat API (Pro): $85/month (2GB RAM, 1 CPU, autoscaling)
Admin API (Pro): $85/month (2GB RAM, 1 CPU)
Admin UI (Starter): $25/month
PostgreSQL (Pro): $95/month (4GB RAM, PITR)
Total: ~$290/month
```

### Features

**Included**:
- Zero-downtime deploys
- Automatic SSL/TLS certificates
- DDoS protection
- Health checks and auto-restart
- Build pipeline with CI/CD
- Private networking between services
- Managed PostgreSQL with backups
- Git-based deployment workflow
- Global CDN
- Free staging environments

**Limitations**:
- Fixed resource tiers (can't fine-tune)
- No control over underlying infrastructure
- Limited to Render's supported regions
- Can't use all Kubernetes features
- Autoscaling less granular than K8s HPA

### Multi-Tenant Database Support

**Works with shared-app-dedicated-db architecture**:
- Single PostgreSQL instance can host multiple databases
- Application connects to different databases dynamically
- Same TenantEngineManager pattern works
- Each tenant gets dedicated database on shared PostgreSQL instance

**Example `render.yaml`**:
```yaml
services:
  - type: web
    name: salient-backend
    runtime: docker
    dockerfilePath: ./Dockerfile
    plan: pro
    numInstances: 3
    envVars:
      - key: POSTGRES_ADMIN_URL
        fromDatabase:
          name: salient-postgres
          property: connectionString
      - key: EXPOSED_ROUTERS
        value: all

databases:
  - name: salient-postgres
    plan: pro
    databaseName: salient_admin
    # Create additional databases via dashboard or CLI:
    # - tenant_a
    # - tenant_b
    # - tenant_c
```

**Managing Multiple Databases**:
```bash
# Create tenant databases via Render CLI or dashboard
# All databases share same PostgreSQL instance
# Connection strings: postgresql://{host}/{database_name}
```

### Pros

- ✅ Simplest deployment model (git push to deploy)
- ✅ Lowest operational burden
- ✅ Fast time to market
- ✅ Transparent, predictable pricing
- ✅ Managed PostgreSQL with automatic backups
- ✅ Free staging environments
- ✅ Excellent developer experience
- ✅ Good for small teams (< 10 engineers)
- ✅ Works with shared-app-dedicated-db architecture

### Cons

- ❌ 3-5x markup over raw compute costs
- ❌ Less control over infrastructure
- ❌ Autoscaling less sophisticated than K8s HPA
- ❌ Can't use advanced K8s features (StatefulSets, DaemonSets, custom operators)
- ❌ Limited regions (vs AWS/GCP global reach)
- ❌ Fixed resource tiers (vs K8s flexible resource allocation)
- ❌ Migration to Kubernetes later requires rewrite of deployment configs

### When to Choose Render.com

✅ Team < 5 engineers
✅ MVP or early stage product
✅ Want to focus on product, not infrastructure
✅ Limited DevOps expertise
✅ Budget < $500/month
✅ Can accept 3-5x cost premium for simplicity
✅ Don't need advanced K8s features
✅ Want fastest time to market

### When NOT to Choose Render.com

❌ Team has strong DevOps/K8s expertise
❌ Need fine-grained resource control
❌ Budget > $1,000/month (K8s becomes more cost-effective)
❌ Scaling to 50+ tenants
❌ Need advanced features (custom networking, operators)
❌ Require multi-region with custom routing
❌ Want to avoid vendor lock-in

### Linode/Akamai LKE (Linode Kubernetes Engine)

**Control Plane**: Free (Standard) or Paid (Enterprise)
**Worker Nodes**: Linode pricing varies by plan
**PostgreSQL**: Managed Database powered by Aiven

**Pricing Example (Small Production)**:
```
Control Plane: $0 (Standard tier)
3 × Linode 4GB: $24 × 3 = $72/month
Managed PostgreSQL (Aiven, 2GB): ~$50/month
Load Balancer: $10/month
Block Storage (100GB): $10/month
Total: ~$142/month
```

**Pros**:
- Free control plane (standard tier)
- Competitive pricing (between DOKS and big three)
- Strong performance reputation
- Good global presence
- Akamai CDN integration
- Enterprise tier available (dedicated control plane)

**Cons**:
- Managed database uses Aiven (third-party integration)
- Smaller community than big three
- Fewer integrations than AWS/GCP/Azure
- Documentation less comprehensive

**Best For**: Teams wanting balance of cost and features, organizations needing CDN integration, international deployments.

### Vultr VKE (Vultr Kubernetes Engine)

**Control Plane**: Free
**Worker Nodes**: Vultr compute pricing
**PostgreSQL**: Managed Database starts at $15/month

**Pricing Example (Small Production)**:
```
Control Plane: $0 (free)
3 × Regular Performance (2GB/1vCPU): $12 × 3 = $36/month
Managed PostgreSQL (2GB): $15/month
Load Balancer: $10/month
Block Storage (100GB): $10/month
Total: ~$71/month
```

**Pros**:
- Lowest overall cost
- Free control plane
- 32 global locations
- Good performance
- Simple pricing

**Cons**:
- Smaller provider (less established)
- Limited ecosystem
- Fewer managed services
- Smaller community
- Less documentation

**Best For**: Ultra cost-conscious deployments, international presence needed, experimental/side projects.

## PostgreSQL Deployment Options

### Option 1: Managed Database (Recommended)

**Pros**:
- Automated backups and point-in-time recovery
- Automatic minor version updates
- High availability with automatic failover
- Monitoring and alerting included
- No maintenance burden

**Cons**:
- Higher cost than self-managed
- Less control over configuration
- Potential vendor lock-in

**Providers**:
- AWS RDS: $15-$150+/month
- Google Cloud SQL: $10-$100+/month
- Azure Database: $25-$120+/month
- DigitalOcean: $15-$55/month (HA)
- Linode/Akamai: $50+/month (Aiven)
- Vultr: $15+/month

### Option 2: PostgreSQL in Kubernetes (StatefulSet)

**Pros**:
- Full control over configuration
- Lower cost (just storage costs)
- Same infrastructure as application

**Cons**:
- Must manage backups manually
- High availability complex to configure
- Storage performance critical
- Upgrade complexity
- Requires database expertise
- Risk of data loss if not done correctly

**Cost Example**:
```
Persistent Volume (100GB SSD): $10/month
No additional database service cost
```

**Operators Available**:
- Zalando Postgres Operator
- CloudNativePG
- Crunchy Data PGO

### Option 3: External Managed PostgreSQL (Separate Provider)

Use database provider separate from Kubernetes host:

**Examples**:
- Neon (serverless PostgreSQL)
- Supabase (PostgreSQL with additional features)
- ElephantSQL
- Aiven

**Pros**:
- Decouple database from compute
- Specialized database expertise
- Can switch K8s provider independently

**Cons**:
- Network latency (different providers)
- Two vendors to manage
- Potential egress charges

## Cost Comparison Matrix (Including Render.com)

| Provider | Control Plane | 3 Nodes (4GB) | PostgreSQL (HA) | Load Balancer | Storage (100GB) | **Total/Month** |
|----------|--------------|---------------|-----------------|---------------|-----------------|-----------------|
| **Render.com** | Included | $75 | $25-95 | Included | Included | **$100-170** |
| **Vultr** | $0 | $36 | $15 | $10 | $10 | **$71** |
| **DigitalOcean** | $0 | $126 | $55 | $12 | $20 | **$213** |
| **Linode/Akamai** | $0 | $72 | $50 | $10 | $10 | **$142** |
| **Azure AKS** | $0 | $90 | $120 | $20 | $10 | **$240** |
| **Google GKE** | $0 | $144 | $100 | $18 | $17 | **$279** |
| **AWS EKS** | $72 | $90 | $150 | $18 | $10 | **$340** |

**Note**: Render.com is not directly comparable (PaaS vs IaaS), but included for reference. Prices are estimates for small production workloads.

## Feature Comparison

| Feature | Render.com | AWS EKS | Google GKE | Azure AKS | DigitalOcean | Linode | Vultr |
|---------|------------|---------|------------|-----------|--------------|--------|-------|
| **Deployment Model** | PaaS | K8s | K8s | K8s | K8s | K8s | K8s |
| **Control Plane Cost** | Included | ❌ $72/mo | ✅ Free | ✅ Free | ✅ Free | ✅ Free | ✅ Free |
| **Ease of Use** | ✅ Simplest | ⚠️ Complex | ✅ Good | ⚠️ Moderate | ✅ Excellent | ✅ Good | ✅ Good |
| **Managed DB Quality** | ✅ Good | ✅ Excellent | ✅ Excellent | ✅ Excellent | ✅ Good | ⚠️ Third-party | ⚠️ Basic |
| **Auto-Scaling** | ⚠️ Basic | ✅ Full | ✅ Full | ✅ Full | ✅ Good | ✅ Good | ✅ Good |
| **Monitoring** | ✅ Built-in | ⚠️ Extra cost | ✅ Included | ⚠️ Extra setup | ✅ Included | ✅ Included | ✅ Included |
| **Global Reach** | ⚠️ Limited | ✅ 25+ regions | ✅ 25+ regions | ✅ 60+ regions | ⚠️ 15 regions | ✅ 25+ regions | ✅ 32 regions |
| **Ecosystem** | ⚠️ Limited | ✅ Largest | ✅ Large | ✅ Large | ⚠️ Smaller | ⚠️ Smaller | ⚠️ Smaller |
| **Documentation** | ✅ Excellent | ✅ Extensive | ✅ Excellent | ✅ Good | ✅ Good | ⚠️ Adequate | ⚠️ Adequate |
| **Community** | ⚠️ Growing | ✅ Largest | ✅ Large | ✅ Large | ⚠️ Smaller | ⚠️ Smaller | ⚠️ Smallest |
| **Support** | ✅ Good | ✅ Enterprise | ✅ Enterprise | ✅ Enterprise | ✅ Good | ✅ Good | ⚠️ Basic |
| **DevOps Required** | ✅ None | ❌ High | ⚠️ Moderate | ⚠️ Moderate | ⚠️ Basic | ⚠️ Basic | ⚠️ Moderate |
| **Infrastructure Control** | ❌ None | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |

## Multi-Tenant Database Support

All providers support the shared-app-dedicated-db architecture:

| Provider | Managed PostgreSQL | Multiple Databases | Connection Pooling | Cost-Effective |
|----------|-------------------|-------------------|-------------------|----------------|
| **AWS** | ✅ RDS | ✅ Yes | ✅ RDS Proxy ($15/mo) | ⚠️ Higher cost |
| **GCP** | ✅ Cloud SQL | ✅ Yes | ✅ Built-in | ✅ Moderate |
| **Azure** | ✅ Azure Database | ✅ Yes | ✅ Built-in | ✅ Moderate |
| **DigitalOcean** | ✅ Managed DB | ✅ Yes | ✅ PgBouncer | ✅ Best value |
| **Linode** | ✅ Aiven | ✅ Yes | ✅ PgBouncer | ✅ Good value |
| **Vultr** | ✅ Managed DB | ✅ Yes | ✅ PgBouncer | ✅ Lowest cost |

**Note**: All providers support creating multiple databases on a single PostgreSQL instance, which is essential for the shared-app-dedicated-db architecture.

## Detailed Cost Scenarios

### Scenario A: MVP / Early Stage (Low Traffic)

**Requirements**: 2-3 pods, < 1000 requests/day, 1-3 tenants

| Provider | Monthly Cost | Best For |
|----------|--------------|----------|
| **Render.com** | $100-170 | Fastest to market, no DevOps needed |
| **Vultr** | $71 | Absolute lowest cost, basic features |
| **DigitalOcean** | $106 | Best balance (K8s) |
| **Linode** | $142 | Good middle ground |
| **Azure AKS** | $240 | Already using Azure |
| **Google GKE** | $279 | Kubernetes expertise on team |
| **AWS EKS** | $340 | Already using AWS |

**Recommendation**: 
- **Render.com** if you want simplest deployment and have < 5 engineers
- **DigitalOcean K8s** if you want Kubernetes control without complexity

### Scenario B: Growth Stage (Medium Traffic)

**Requirements**: 5-10 pods with auto-scaling, 10,000-50,000 requests/day, 10-20 tenants

| Provider | Monthly Cost | Notes |
|----------|--------------|-------|
| **Render.com** | $250-400 | Still simple, but cost premium grows |
| **Vultr** | $150-200 | Still lowest cost but limited support |
| **DigitalOcean** | $300-400 | Good scaling, simple operations |
| **Linode** | $350-450 | Solid performance, Akamai CDN |
| **Azure AKS** | $500-600 | Good if using Azure services |
| **Google GKE** | $600-700 | Autopilot mode valuable here |
| **AWS EKS** | $700-900 | Most expensive but most features |

**Recommendation**: 
- **Render.com** if you still don't have DevOps resources
- **DigitalOcean K8s** if cost matters and you've built K8s expertise
- Consider migrating from Render → DOKS at this stage if cost becomes concern

### Scenario C: Enterprise / Scale (High Traffic)

**Requirements**: 20-50 pods, 500,000+ requests/day, 50+ tenants, multi-region

| Provider | Monthly Cost | Notes |
|----------|--------------|-------|
| **AWS EKS** | $2,000-3,000 | Best enterprise features, global reach |
| **Google GKE** | $1,800-2,500 | Excellent Kubernetes native features |
| **Azure AKS** | $1,500-2,200 | Strong enterprise integration |
| **DigitalOcean** | $1,000-1,500 | Still cost-effective but scaling limits |
| **Linode** | $1,200-1,700 | Good value at scale |
| **Vultr** | $800-1,200 | Lowest cost but less support |
| **Render.com** | N/A | Not suitable for enterprise scale |

**Recommendation**: **AWS EKS** or **Google GKE** - Enterprise features, global reach, and support justify higher cost. Render.com not recommended at this scale.

## Decision Framework

### Choose Render.com (PaaS) If:
✅ Team < 5 engineers with no DevOps expertise
✅ MVP stage, need to ship fast
✅ Want zero infrastructure management
✅ Budget < $500/month
✅ Can accept 3-5x cost premium for simplicity
✅ Don't need advanced K8s features
✅ Priority is speed to market over cost optimization

### Choose AWS EKS If:
✅ Already using AWS services (S3, Lambda, etc.)
✅ Need deep AWS integration (IAM, VPC, etc.)
✅ Enterprise requirements (compliance, support)
✅ Budget is not primary concern
✅ Team has AWS expertise
✅ Need maximum feature set

### Choose Google GKE If:
✅ Want most Kubernetes-native experience
✅ Value automation (Autopilot mode)
✅ Team has Kubernetes expertise
✅ Need excellent monitoring
✅ Budget is moderate
✅ Using Google Cloud services

### Choose Azure AKS If:
✅ Already using Azure services
✅ Need Active Directory integration
✅ Microsoft/Enterprise stack
✅ Want free control plane
✅ Budget is moderate

### Choose DigitalOcean If:
✅ Startup/small business (< 50 employees)
✅ MVP to growth stage
✅ Cost is primary concern
✅ Team has limited Kubernetes expertise
✅ Want simple operations
✅ Need fast setup
✅ **This is the sweet spot for most startups**

### Choose Linode/Akamai If:
✅ Need good price/performance balance
✅ Want Akamai CDN integration
✅ International deployment
✅ Value reliability reputation
✅ Don't need cutting-edge features

### Choose Vultr If:
✅ Absolute lowest cost is critical
✅ Experimental/side project
✅ Need many global locations
✅ Comfortable with smaller provider
✅ Don't need extensive support

## Recommended Path

### Phase 1: MVP (0-6 months)

**Option A (Recommended): Render.com (PaaS)**
**Cost**: ~$100-200/month
**Justification**:
- Zero DevOps overhead
- Ship product fastest
- Learn customer needs before optimizing infrastructure
- Easy to migrate to K8s later (standard Docker)
- Works with shared-app-dedicated-db architecture

**Option B: DigitalOcean Kubernetes**
**Cost**: ~$100-200/month
**Justification**:
- Free control plane saves $72/month vs AWS
- More control than Render.com
- Choose this if you have K8s expertise on team
- Slightly more setup but lower long-term costs

### Phase 2: Growth (6-18 months)

**Platform**: DigitalOcean Kubernetes or Linode LKE
**Cost**: ~$300-600/month
**When to migrate from Render.com**:
- Monthly cost exceeds $500
- Need more control over autoscaling
- Want to reduce per-resource costs
- Have hired DevOps engineer

**Decision Factors if already on K8s**:
- If scaling smoothly: Stay on DigitalOcean
- If need advanced features: Migrate to GKE (best K8s) or AKS (lowest fixed cost)
- If already on AWS for other services: Migrate to EKS

### Phase 3: Scale (18+ months)

**Platform**: AWS EKS, Google GKE, or Azure AKS
**Cost**: $1,000-3,000+/month
**Justification**:
- Enterprise features needed
- Multi-region deployment
- Advanced auto-scaling
- Dedicated support
- Compliance requirements

## Alternative: Hybrid Approach

**Control Plane**: Managed Kubernetes (DigitalOcean or Linode)
**Database**: External managed PostgreSQL (Neon, Supabase, Aiven)
**CDN/Edge**: Cloudflare

**Benefits**:
- Best-in-class for each component
- Easy to migrate K8s provider
- Database independent of compute
- Global CDN performance

**Drawbacks**:
- Multiple vendors to manage
- Potential network latency
- More complex operations

## Summary

**For Salient Backend (Multi-Tenant with Dedicated DBs)**:

### Immediate Recommendation: **Render.com (PaaS)**

**Why start with Render.com**:
1. **Fastest to market**: Deploy in hours, not days
2. **Zero DevOps burden**: No K8s expertise required
3. **Cost-effective for MVP**: ~$100-200/month for 1-3 tenants
4. **Works with architecture**: Supports shared-app-dedicated-db pattern
5. **Easy migration path**: Standard Docker makes K8s migration straightforward
6. **Focus on product**: Build features and find product-market fit first

### Growth Path: **Migrate to DigitalOcean Kubernetes**

**When to migrate** (typically 6-12 months):
- Monthly Render costs exceed $500
- Need more granular autoscaling control
- Have 10-20+ tenants
- Hired DevOps engineer or built K8s expertise

**Why DigitalOcean K8s for growth**:
1. **Cost**: ~$300-500/month for 10-20 tenants (vs $800-1000 on Render)
2. **Simplicity**: Still simpler than AWS EKS / GKE / AKS
3. **Managed PostgreSQL**: Built-in support for multiple databases per instance
4. **Sufficient features**: HPA, load balancer, monitoring, backups included
5. **Scaling path**: Can handle 50+ tenants before needing enterprise K8s

### Long-term: **AWS EKS or Google GKE** (if needed)

**When to migrate** (typically 18+ months):
- Scaling to 50+ tenants
- Multi-region deployment required
- Need enterprise compliance (SOC2, HIPAA, etc.)
- Advanced features needed (service mesh, custom operators)

**Secondary Options**:
- **Linode LKE**: If need better international presence or CDN integration
- **Vultr**: If budget is extremely constrained (<$100/month) and willing to sacrifice support

**Not Recommended**:
- **Starting with AWS EKS**: $72/month control plane premium not justified for MVP
- **Azure AKS**: Only if already committed to Azure ecosystem
- **Self-Managed K8s**: Operational burden too high for small team

**Key Insight**: The 3-5x cost premium of Render.com vs raw K8s is worth it during MVP stage. You save weeks of DevOps work and can focus on product. Migrate to K8s once you have revenue and know the architecture works.
