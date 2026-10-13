# MongoDB Atlas Security Hardening Guide (RestockIQ)

## 1. Overview & Current Posture
During local development and multi-device testing (e.g., physical Android phones on cellular networks, Flutter local emulators, remote developers), MongoDB Atlas is often configured with an entry of `0.0.0.0/0` (Allow Access from Anywhere) in the IP Access List.

> **Tradeoff Assessment:**
> - **Demo / Prototyping:** Conscious demo tradeoff allowing fast cross-network testing without constant IP renegotiation.
> - **Production Deployment:** `0.0.0.0/0` is a high security risk if credentials are leaked. Production instances MUST lock down access to designated egress IPs or private network peering.

---

## 2. Step-by-Step Production Lockdown

### Step 1: Determine Egress IPs of the Backend Host
Identify where the FastAPI container is deployed:
- **Render / Railway / Fly.io:** Check the platform dashboard for outbound/egress static IP addresses (or static egress proxy add-ons such as Fixie / QuotaGuard Static).
- **AWS (ECS / EC2 / EKS):** Use the Elastic IP (EIP) assigned to your NAT Gateway attached to the private subnet running your containers.
- **GCP (Cloud Run / GKE):** Configure a Serverless VPC Access connector routed through a Cloud NAT with a reserved static external IP.

### Step 2: Update Atlas Network Access List
1. Navigate to [cloud.mongodb.com](https://cloud.mongodb.com) and log in.
2. Select your Project and Cluster (`Cluster0`).
3. In the left navigation sidebar under **Security**, click **Network Access**.
4. In the **IP Access List** tab:
   - Locate the entry `0.0.0.0/0` (or `Allow Access from Anywhere`).
   - Click **Actions (...) -> Delete** and confirm deletion.
5. Click **Add IP Address**:
   - Enter the egress IP or CIDR block of your backend deployment host (e.g., `35.240.12.34/32`).
   - Provide a clear label (e.g., `Production Backend Host - Cloud Run`).
   - Click **Confirm**.

### Step 3: Enterprise Alternative: VPC Peering or PrivateLink
For maximum production security without exposing port 27017 to the public internet:
1. In Atlas, go to **Network Access -> Private Network Peering** or **Private Endpoint**.
2. Set up a peering connection between your VPC (AWS VPC / GCP VPC / Azure VNet) and Atlas.
3. This ensures all database queries travel exclusively over private cloud backbones with zero public internet exposure.

---

## 3. Database User Least-Privilege & Auditing
1. In **Security -> Database Access**, ensure the application user (`lucifer940oy_db_user`) has only `readWrite` permissions on the `restockiq` database (not `readWriteAnyDatabase` or `atlasAdmin`).
2. Enforce SCRAM-SHA-256 authentication and rotate database user passwords periodically.
3. Never commit raw connection strings into Git repositories (enforce through `.env` and secret managers).
