# Modal Pricing — Hermes Sandbox Backend

Source: https://modal.com/pricing (verified 2026-07-11). Sandbox tier = 3× standard Functions tier.

## Per-second rates (Sandbox)
| Resource | Rate | Notes |
|---|---|---|
| CPU | $0.0000131 / core / s | min 0.125 core |
| Memory | $0.00000222 / GiB / s | |
| GPU T4 | $0.000164 / s | up to H100 $0.001097/s |
| Volume | $0.09 / GiB / mo | 1 TiB free |

## Plans
| Plan | Price | Credit/mo | Limits |
|---|---|---|---|
| Starter | $0 | **$30 free** | 100 containers, 10 GPU concurrency, 3 seats |
| Team | $250 | $100 | 1000 containers, 50 GPU concurrency |
| Enterprise | custom | custom | audit logs, SSO, HIPAA |

- Credit is **monthly, use-or-lose**.
- Region selection adds 1.5–1.75× base; non-preemptible 3×.

## Cost model for our usage (no GPU)
Formula per task: (cores × $0.0000131 + GiB × $0.00000222) × seconds.

| Profile | Compute | Cost/task | #/mo in $30 |
|---|---|---|---|
| Light | 1 core, 30s | ~$0.0012 | ~25,000 |
| Typical | 2 cores, 2 min | ~$0.0094 | ~3,200 |
| Heavy | 4 cores, 5 min | ~$0.047 | ~630 |

## Reference point
Calypso Hetzner bill ≈ €2.30/mo (24/7 idle, did little). On Modal that fits inside the **$30 Starter free credit → €0.00 out of pocket**, and you pay only for actual compute seconds.

## Caveat
$30 is a generous ceiling for an agent idle-between-tasks. Real spend unknown until measured — recommend a weekly spend check for the first month.
