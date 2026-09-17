# Cost Trade-offs: Free-Tier-Safe Architecture vs Real Production

This deployment deliberately skips two components that a real production
environment would include, purely to stay within AWS Free Tier limits for
this practice/demo build.

## 1. NAT Gateway (not used here)

**What we did instead:** App instances run in public subnets with public IPs,
protected by security groups that only allow inbound traffic on 22 (SSH) and
8080 (from the ALB security group only) — so network isolation is still
enforced at the security-group layer, even without private subnets.

**Why a real production setup uses a NAT Gateway:**
- App/database instances belong in private subnets with no direct route to
  the internet — reducing the attack surface (no public IP to scan/target).
- A NAT Gateway lets those private instances still reach the internet
  *outbound* (e.g. pulling OS package updates, hitting external APIs,
  downloading dependencies) without being reachable *inbound*.
- Security groups alone stop unwanted inbound traffic, but they don't hide
  the instance — it still has a public IP and is discoverable. Defense in
  depth means layering private subnets + NAT on top of security groups, not
  relying on security groups as the only control.
- Compliance frameworks (PCI-DSS, SOC 2, HIPAA) generally require that
  application and database tiers not be directly internet-routable.

**Cost reason we skipped it:** NAT Gateway charges an hourly rate plus
per-GB data processing charges — it's one of the few core networking
primitives *not* covered by the AWS Free Tier, and for a short-lived demo
it would add a small but real cost from minute one.

## 2. RDS Multi-AZ (not used here)

**What we did instead:** RDS runs Single-AZ (`multi_az = false` in
`terraform/modules/database`), with automated backups (1-day retention) and
strict network isolation (only the app tier's security group can reach
port 5432).

**Why a real production setup uses Multi-AZ:**
- Multi-AZ maintains a synchronously-replicated standby in a second
  Availability Zone. If the primary AZ has an outage (or the instance itself
  fails), RDS automatically fails over to the standby — typically within
  60–120 seconds — with no manual intervention and no data loss for
  committed transactions.
- Single-AZ has no automatic failover: an AZ outage or instance failure
  means restoring from the latest automated backup, which has both a
  recovery-time cost (minutes to hours) and a potential data-loss window
  (anything written since the last backup/transaction log).
- For a stateful, business-critical database, the extra cost buys
  significantly higher availability and removes a single point of failure
  from the architecture.

**Cost reason we skipped it:** Multi-AZ roughly doubles the RDS instance-hour
cost (you're paying for two instances, primary + standby) and is not
Free-Tier eligible beyond the single free-tier-eligible instance. For this
demo, Single-AZ keeps the whole stack inside free-tier limits.

## Summary

| Component | This build | Real production | Why the difference |
|---|---|---|---|
| App subnets | Public, SG-restricted | Private, behind NAT | Cost: NAT Gateway not free-tier eligible |
| RDS | Single-AZ | Multi-AZ | Cost: Multi-AZ ~2x instance cost, not free-tier eligible |

Both trade-offs are documented here specifically so they're a conscious,
explained decision — not an oversight. In a real production deployment,
enabling both would be one Terraform variable change each
(`enable_nat_gateway = true`, `multi_az = true` in the respective modules).
