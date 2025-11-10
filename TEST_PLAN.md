# FinCube Performance Test Plan

This document outlines the comprehensive performance testing strategy for FinCube, focusing on Web3 DAO proxy services, onchain-offchain synchronization and RPC endpoints.

## Test Objectives

### Primary Objectives

- **Validate transaction throughput** under various load conditions
- **Measure response times** for critical blockchain operations
- **Identify system bottlenecks** in DAO Service, Audit Trail Service and User Management Service
- **Ensure transaction confirmation reliability** during high-load scenarios
- **Assess RPC endpoint performance** (Alchemy, The Graph)
- **Evaluate scalability** with increasing number of services, event frequency, and dApp features
- **Assess consistency** between on-chain events and off-chain state

### Performance Goals

- **Transaction Processing**: Handle 150+ transactions with 99% success rate
- **Response Time**: < 2 seconds for POST requests under normal load
- **Confirmation Time**: All transactions confirmed within 20 seconds
- **System Stability**: Zero service crashes during testing
- **Resource Utilization**: CPU < 80%, Memory < 85% during peak load

## Test Scope

### In Scope

- **DAO Service endpoints** (`/dao-service/proposal-service`)
- **RPC Endpoints** (Alchemy Sepolia, The Graph Studio)
- **Load, Stress, and Spike testing scenarios**
- **Network confirmation delays**
- **End-to-end transaction processing**
- **Event handling and logging**
- **On-chain and off-chain state synchronization**

### Out of Scope

- Frontend UI performance
- Database performance (non-blockchain)
- Third-party service availability beyond RPC providers
- Security testing
- Cross-browser compatibility

## Test Environment

### Infrastructure

- **Target Environment**: `http://localhost:3000` (local) and `http://172.16.231.80:3000` (remote)
- **Blockchain Network**: Ethereum Sepolia Testnet
- **RPC Provider**: Alchemy (`https://eth-sepolia.g.alchemy.com/v2/<rpc-secrret>`)
- **Graph Protocol**: The Graph Studio
- **Load Testing Tool**: k6

### Test Data

- **Total Transactions**: 1800
- **Virtual Users**: 1-50 (depending on test type)

## Test Items & Endpoints

### Primary Endpoints

- **(POST)** `http://localhost:3000/dao-service/proposal-service`

### RPC Endpoints

- **Alchemy Sepolia**: `eth_blockNumber` method calls
- **The Graph Studio**: Latest block queries

## Performance Metrics

### Key Performance Indicators

- **Transaction Latency**: Time between transaction submission and confirmation
- **Throughput**: Number of transactions/requests processed per second
- **Resource Utilization**: CPU, memory, and network usage during tests
- **Log Processing Time**: Time taken to process and store logs/events
- **Scalability**: System behavior under increasing load
- **Consistency**: Accuracy of off-chain state compared to on-chain events
- **Success Rate**: Percentage of successful requests/transactions

### Response Time Targets

| Operation                | Target (avg) | Acceptable (p95) |
| ------------------------ | ------------ | ---------------- |
| POST Requests            | < 1s         | < 2s             |
| GET Requests             | < 500ms      | < 1s             |
| Transaction Confirmation | < 20s        | < 30s            |
| RPC Calls                | < 500ms      | < 2s             |

## Test Scenarios

### 1. Load Testing (Normal Operations)

```
Objective: Test normal operating conditions
- Duration: 10 minutes
- Virtual Users: 10-15 constant load
- Request Pattern: Steady, consistent load
- Transaction Batches: 10 batches of 15 transactions each
- Confirmation Delay: 20 seconds between batches
- Expected: 99%+ success rate, stable response times
```

### 2. Stress Testing (Breaking Point)

```
Objective: Find system breaking point
- Duration: 15 minutes
- Virtual Users: Ramp up 0 → 50 → 0
- Request Pattern: Gradual increase to maximum capacity
- Transaction Volume: 300+ transactions
- Expected: Identify maximum sustainable load
```

### 3. Spike Testing (Traffic Surges)

```
Objective: Test sudden traffic increases
- Duration: 5 minutes
- Virtual Users: 0 → 50 → 0 (rapid changes)
- Request Pattern: Sudden spikes and drops
- Transaction Volume: Variable bursts
- Expected: System recovers gracefully, no crashes
```

### 4. RPC Endpoint Validation

```
Objective: Validate external service dependencies
- Alchemy RPC: 100 eth_blockNumber calls
- The Graph: 100 latest block queries
- Load Pattern: 10 VUs, 10 iterations each
- Success Criteria: 99%+ success rate, < 2s response time
```

### 5. Extended Load Testing

```
Objective: Long-duration stability testing
- Duration: 30 minutes
- Virtual Users: 5-10 constant
- Request Pattern: Sustained moderate load
- Expected: No memory leaks, consistent performance
```

## Test Execution Strategy

### Pre-Test Setup

1. Verify all endpoints are accessible
2. Validate RPC connection limits

### Test Sequence

1. **RPC Baseline Tests** → Validate external dependencies
2. **Load Testing** → Establish baseline performance
3. **Stress Testing** → Find system limits
4. **Spike Testing** → Test resilience
5. **Extended Load** → Stability validation
6. **Consistency Checks** → Verify data integrity

## Success Criteria

### Performance Benchmarks

| Metric              | Green Zone | Yellow Zone | Red Zone |
| ------------------- | ---------- | ----------- | -------- |
| Response Time (avg) | < 1s       | 1-2s        | > 2s     |
| Success Rate        | > 99%      | 95-99%      | < 95%    |
| Concurrent Users    | 1-15       | 16-30       | 31+      |
| CPU Utilization     | < 60%      | 60-80%      | > 80%    |
| Memory Usage        | < 70%      | 70-85%      | > 85%    |

## Test Tools & Scripts

### k6 Test Scripts

```
rpc-tests.js/
├── alchemy-test.js     # Alchemy RPC endpoint validation
└── graph-test.js       # The Graph Protocol testing

test-methods/
├── onchain-sync.js        # Onchain and Offchain event synchronization
```

### Monitoring & Reporting

- **k6 built-in metrics** (response times, throughput, errors)
- **System monitoring** (`htop`, `docker stats`, cloud dashboards)
- **Custom Grafana dashboard** (`dashboards/primary-dashboard.json`)

## Actual Test Execution & Results

### Tests Completed

#### 1. Onchain Synchronization Performance Tests ✅

**Test Configuration:**

- **Virtual Users**: 30 concurrent users
- **Total Iterations**: 1200 transactions per test run
- **Test Duration**: 15 minutes maximum
- **Transaction Source**: 2500 unique Etherscan transactions
- **Test Variants**: 1200, 1400, 1600, 1800 transaction loads

**Test Script:** `test-methods/onchain-sync.js`

**Endpoints Tested:**

- DAO Service: `http://172.16.231.80:3000/dao-service/proposal-service`

#### 3. RPC Endpoint Validation ✅

**Scripts Available:**

- `rpc-tests/alchemy-test.js` - Alchemy Sepolia endpoint validation
- `rpc-tests/graph-test.js` - The Graph Protocol testing

### Test Infrastructure

**Environment Setup:**

- Python 3.12 with virtual environment (`.venv`)
- Required packages: pandas, numpy, matplotlib, seaborn, scipy
- k6 load testing tool installed
- InfluxDB (Docker) for metrics storage
- Grafana (Docker) for visualization

**Monitoring:**

- Primary Grafana dashboard: `dashboards/primary-dashboard.json`
- InfluxDB database: `k6`
- Real-time metrics collection during test execution

### Analysis Capabilities

**Performance Analysis Script:** `scripts/analyze_performance.py`

**Capabilities:**

- Automatic time unit detection (ns, us, ms, s)
- Bootstrap confidence intervals for percentiles
- CDF plots for latency distribution
- Time-series throughput and latency analysis
- Comparative analysis (Fincube vs baseline)
- Error rate calculation
- Per-second metrics aggregation

**Features:**

- Auto-detection of column names
- Flexible input options
- Multiple load comparison
- Publication-quality plots (150 DPI)
- Comprehensive statistical metrics (p50, p90, p95, p99 with CIs)

### Performance Insights & Recommendations

**Strengths:**

- ✅ Very high success rate (98.67%)
- ✅ Robust synchronization mechanism
- ✅ Complete trace coverage for successful transactions
- ✅ Handles 300+ concurrent syncs effectively

**Areas for Improvement:**

- ⚠️ High sync duration variability (324s standard deviation)
- ⚠️ Tail latency optimization needed (some >1000s syncs)
- ⚠️ 4 failed synchronizations require investigation
- ⚠️ Pending source transitions need retry logic

**Recommended SLAs:**

- **Target Success Rate**: Maintain >98%
- **P50 Duration Target**: <420 seconds (7 minutes)
- **P95 Duration Target**: <800 seconds (13 minutes)
- **P99 Duration Target**: <1000 seconds (16 minutes)
