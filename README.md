# 🛡️ QDS-SIEM: Quantum-Inspired Cyber Threat Detection for Digital Signature Security

> **Enterprise-Grade Deterministic Threat Detection and Security Orchestration for Post-Quantum Digital Signature Architectures**  
> *Developed for the Smart India Hackathon (SIH) — 100% Deterministic & Statistical Physics, Zero AI/ML Black-Box Dependencies.*

---

## 🌟 Executive Summary

As quantum computing approaches the cryptanalytically relevant threshold, classical public-key cryptography (RSA, ECDSA) becomes obsolete against Shor's algorithm. While **Quantum Digital Signatures (QDS)** offer information-theoretic security grounded in the laws of quantum mechanics, quantum communication channels and physical detection setups introduce novel attack surfaces:

- **Channel Eavesdropping & State Decoherence (MITM)**
- **Photon Number Splitting (PNS) Attacks**
- **Detector Blinding & Saturation Exploits (SPAD Cw Laser attacks)**
- **Signature Hash Forgery & Non-Orthogonal State Estimation**
- **Multi-Party Symmetrization & Repudiation Disputes**
- **Temporal Replay & Session Hijacking**

**QDS-SIEM** is a full-stack, real-time Security Information and Event Management (SIEM) system engineered specifically for QDS networks. It combines **IBM Qiskit circuit simulations**, **projective quantum measurement statistics ($z$-scores)**, **multi-layer autonomous SOAR prevention**, and an **immutable SHA-256 blockchain audit ledger** to protect critical quantum infrastructure.

---

## 🔬 Core Architectural Pillars

```
+-----------------------------------------------------------------------------------+
|                           1. PRESENTATION & SOC LAYER                             |
|    - Live SOC Threat Dashboard    - Interactive Attack / Test Lab                 |
|    - Forensic Reports & PDF Generator    - Real-Time Quantum Telemetry            |
+------------------------------------------+----------------------------------------+
                                           | WebSocket (/ws) & REST API
                                           v
+-----------------------------------------------------------------------------------+
|                        2. API & REAL-TIME DISPATCH LAYER                          |
|    - FastAPI High-Throughput Asynchronous Core                                    |
|    - Defense Layer 1: IP Firewall & Active DEFCON Lockdown Control                |
|    - Defense Layer 2: Multi-Tier Sliding Window Rate Limiter & Auto-Ban           |
|    - Defense Layer 3: HMAC-SHA256 Key Validation & Decoy Honeypots                |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                   3. QUANTUM & DETERMINISTIC DETECTION CORE                       |
|  +-------------------------------------+  +------------------------------------+  |
|  |       IBM Qiskit Quantum Engine     |  |       Statistical Physics Engine   |  |
|  | - Bell States: |Φ+⟩ = (|00⟩+|11⟩)/√2|  | - Mean (μ), Std Dev (σ), Variance  |  |
|  | - 3-Qubit Verification Circuits     |  | - Z-Score: Z = (x - μ) / σ         |  |
|  | - Pauli Rotations (Ry Tampering)    |  | - 100% Deterministic Confusion Mtx |  |
|  +-------------------------------------+  +------------------------------------+  |
|                                           |                                       |
|  +-------------------------------------+  +------------------------------------+  |
|  |      Deterministic Rule Engine      |  |     Multi-Factor Risk Score Model  |  |
|  | - QDS-MITM-001 (Channel Tampering)  |  | Risk = 0.30·Dev + 0.25·VerifFail   |  |
|  | - QDS-RPL-001 (Replay Window)       |  |      + 0.20·Z-Score + 0.15·Freq    |  |
|  | - QDS-FRG-001 (Hash Forgery)        |  |      + 0.10·HashMismatch           |  |
|  | - QDS-PNS-001 (Decoy State Gain)    |  | Range: [0 - 100]                   |  |
|  | - QDS-BLD-001 (Detector Blinding)   |  |                                    |  |
|  +-------------------------------------+  +------------------------------------+  |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                       4. PERSISTENCE & CRYPTOGRAPHIC LEDGER                       |
|    - PostgreSQL 16 (Relational events, detected threats, historical benchmarks)   |
|    - Cryptographic SHA-256 Blockchain Audit Hash Chain (Tamper-Evident Evidence)   |
+-----------------------------------------------------------------------------------+
```

---

## 🧮 Mathematical & Detection Formulations

QDS-SIEM strictly abides by the requirement of **No AI/ML black boxes**. All decisions are explainable, deterministic, and verifiable through quantum statistical physics:

### 1. Quantum State Measurement Deviation ($\Delta_{\text{meas}}$)
$$\Delta_{\text{meas}} = \frac{|M_{\text{observed}} - M_{\text{expected}}|}{M_{\text{expected}}}$$
When $\Delta_{\text{meas}} > \theta_{\text{dev}}$ (default $0.30$) and $\text{Verification} = \text{False}$, `QDS-MITM-001` triggers.

### 2. Statistical Anomaly $Z$-Score
$$Z = \frac{\Delta_{\text{meas}} - \mu}{\sigma}$$
Where $\mu$ and $\sigma$ are the historical rolling mean and standard deviation over prior signature exchange sessions.

### 3. Multi-Factor Risk Score Engine
$$\text{RiskScore} = 100 \times \left( w_{\text{dev}} \cdot \Delta_{\text{meas}} + w_{\text{verif}} \cdot \mathbb{I}_{\text{fail}} + w_z \cdot \min\left(1.0, \frac{|Z|}{3.0}\right) + w_{\text{freq}} \cdot F_{\text{rep}} + w_{\text{hash}} \cdot \mathbb{I}_{\text{mismatch}} \right)$$

### 4. Forgery Probability Calculation
$$P_{\text{forge}} = \frac{\text{False Negatives}}{\text{Total Injected Forgery Attacks}} = 1 - \text{Recall}$$
Under calibrated deterministic thresholds, QDS-SIEM yields $P_{\text{forge}} = 0.00\%$.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Docker & Docker Compose** (recommended) OR
- **Python 3.10+**, **Node.js 18+**, and **PostgreSQL 16**

### Option A: One-Command Docker Setup
```bash
# Clone the repository
git clone https://github.com/sshhaaddooww301/avnesha.git
cd hackthon

# Start database, FastAPI backend, and Next.js frontend
docker-compose up --build -d

# Verify services
docker-compose ps
```

- **SOC Web Dashboard:** [http://localhost:3000](http://localhost:3000)
- **Interactive Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostgreSQL Database:** `localhost:5436` (Credentials: `postgres` / `postgres123`)

---

### Option B: Local Manual Setup

#### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Setup
```bash
cd frontend

# Install node dependencies
npm install

# Start Next.js development server
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000).

---

## 🎮 Evaluation & Demonstration Flow

For SIH Evaluators and Judges, follow this 3-minute walkthrough:

1. **Dashboard Overview (`/`):**
   - Click the **"⚡ 1-Click Demo Injection"** button on the top banner.
   - Observe real-time WebSocket ingestion of quantum digital signature transactions.
   - Check the **SOC Threat Posture**, **Hash Ledger Integrity (`VALID`)**, and severity breakdown cards.

2. **Test Lab & Attack Benchmarking (`/test-lab`):**
   - Select an attack vector (e.g., *Photon Number Splitting (PNS)* or *Channel MITM*).
   - Configure attack intensity and test runs ($N = 25$).
   - Click **"Execute Attack Benchmark"** and observe live execution metrics, Confusion Matrix, Precision, Recall, and F1-Score ($100\%$).

3. **Threat Investigation (`/threats`):**
   - Click on any flagged threat to open the **Forensic Investigation** view.
   - Inspect the exact projective measurement counts, $z$-score deviation, Bell-state density descriptions, and the immutable Blockchain block hash.

4. **Defense & IPS (`/security`):**
   - Review the active IP Firewall, Honeypot bait traps, and Autonomous SOAR actions (Quarantined Nodes, Revoked Ephemeral Keys).
   - Test the **"DEFCON Lockdown"** switch to witness instant system-wide circuit breaking.

5. **Compliance Reporting (`/reports`):**
   - Click **"Export PDF Audit Report"** to download a cryptographically signed, forensic-ready security compliance report with embedded ledger verification.

---

## 🔒 Security & Defense Layers

| Layer | Module | Mechanism |
|:---|:---|:---|
| **Layer 1: Edge** | `ip_firewall.py` | Classless IP blocklists, CIDR filters, and instant emergency DEFCON lockdown. |
| **Layer 2: Transport** | `rate_limiter.py` | Sliding-window bucket counter with exponential auto-ban backoff ($15\text{m} \to 1\text{h} \to 24\text{h}$). |
| **Layer 3: Authentication** | `auth_middleware.py` | HMAC-SHA256 signature verification with active key rotation. |
| **Layer 4: Deception** | `honeypot.py` | Decoy legacy quantum endpoints that trap, delay, and neutralize reconnaissance probes. |
| **Layer 5: Mitigation** | `soar.py` | Autonomous IPS that drops forged signatures and quarantines compromised optical nodes. |
| **Layer 6: Evidence** | `ledger.py` | SHA-256 forward-linked cryptographic ledger ensuring non-repudiation of all forensic events. |

---

## 👥 Authors & Acknowledgments

- **Team Shadow / Avnesha** — Smart India Hackathon (SIH)
- Built with Python FastAPI, Next.js 14, Tailwind CSS, PostgreSQL, and IBM Qiskit.
