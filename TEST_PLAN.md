# FinCube Blockchain Performance Test Plan

This document outlines the comprehensive performance testing strategy for the FinCube blockchain application, focusing on Web3 DAO proxy services and RPC endpoints.

## Test Objectives

### Primary Objectives

- **Validate transaction throughput** under various load conditions
- **Measure response times** for critical blockchain operations
- **Identify system bottlenecks** in the Web3 proxy service
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

- **Web3 DAO Proxy Service** (`/web3-dao-proxy/place-proposal`)
- **DAO Service endpoints** (`/dao-service/proposal-service`)
- **RPC Endpoints** (Alchemy Sepolia, The Graph Studio)
- **Transaction batching** (15 transactions per request)
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
- **RPC Provider**: Alchemy (`https://eth-sepolia.g.alchemy.com/v2/XuRKnbPuS-3qwal-CHNdMOcZzOr4PUSB`)
- **Graph Protocol**: The Graph Studio
- **Load Testing Tool**: k6

### Test Data

- **Total Transactions**: 150 per test run
- **Batch Size**: 15 transactions per POST request
- **Confirmation Delay**: 20 seconds between batches
- **Virtual Users**: 1-50 (depending on test type)

## Test Items & Endpoints

### Primary Endpoints

- **(POST)** `http://localhost:3000/web3-proxy-service/web3-dao-proxy/place-proposal`
- **(POST)** `http://localhost:3000/dao-service/proposal-service`
- **(GET)** `http://localhost:3000/dao-service/proposal-service`

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
2. Confirm testnet ETH balance is sufficient
3. Validate RPC connection limits
4. Set up monitoring dashboards

### Test Sequence

1. **RPC Baseline Tests** → Validate external dependencies
2. **Load Testing** → Establish baseline performance
3. **Stress Testing** → Find system limits
4. **Spike Testing** → Test resilience
5. **Extended Load** → Stability validation
6. **Consistency Checks** → Verify data integrity

### Delay Handling

- **20-second delay** after each POST request to `/web3-dao-proxy/place-proposal`
- Allows sufficient time for transaction confirmation
- Prevents overwhelming the blockchain network

## Success Criteria

### Functional Requirements

- ✅ All POST requests return appropriate status codes (200/201)
- ✅ Transaction confirmation rate ≥ 99%
- ✅ Zero data corruption or lost transactions
- ✅ Proper error handling and recovery
- ✅ On-chain and off-chain state consistency

### Performance Benchmarks

| Metric              | Green Zone | Yellow Zone | Red Zone |
| ------------------- | ---------- | ----------- | -------- |
| Response Time (avg) | < 1s       | 1-2s        | > 2s     |
| Success Rate        | > 99%      | 95-99%      | < 95%    |
| Concurrent Users    | 1-15       | 16-30       | 31+      |
| CPU Utilization     | < 60%      | 60-80%      | > 80%    |
| Memory Usage        | < 70%      | 70-85%      | > 85%    |

## Risk Assessment & Mitigation

### High Risk Items

- **Blockchain network congestion** → Use Sepolia testnet, monitor network status
- **RPC rate limiting** → Monitor usage, implement backoff strategies
- **Transaction fee depletion** → Maintain adequate testnet ETH balance

### Medium Risk Items

- **Network latency variations** → Run tests during consistent network conditions
- **Third-party service outages** → Have backup RPC endpoints configured
- **Insufficient test duration** → Allocate buffer time for extended testing

## Test Tools & Scripts

### k6 Test Scripts

```
rpc-tests.js/
├── alchemy-test.js     # Alchemy RPC endpoint validation
└── graph-test.js       # The Graph Protocol testing

test-methods/
├── load-test.js        # Transaction batch load testing
├── stress-test.js      # High-load breaking point testing
└── spike-test.js       # Traffic surge simulation
```

### Monitoring & Reporting

- **k6 built-in metrics** (response times, throughput, errors)
- **System monitoring** (`htop`, `docker stats`, cloud dashboards)
- **Custom Grafana dashboard** (`dashboards/primary-dashboard.json`)
- **Consistency validation scripts** for on-chain vs off-chain state

## Test Schedule & Deliverables

### Execution Timeline

| Phase              | Duration | Activities                          |
| ------------------ | -------- | ----------------------------------- |
| **Setup**          | 4 hours  | Environment prep, script validation |
| **RPC Testing**    | 2 hours  | Endpoint baseline validation        |
| **Load Testing**   | 4 hours  | Normal operation scenarios          |
| **Stress Testing** | 4 hours  | Breaking point identification       |
| **Analysis**       | 8 hours  | Results analysis and documentation  |

### Expected Deliverables

- **Performance Test Summary Report**
- **System Bottleneck Analysis**
- **Scalability Recommendations**
- **Monitoring Dashboard Export**
- **Test Execution Logs & Metrics**

---

**Document Version**: 2.0  
**Last Updated**: August 11, 2025  
**Prepared for**: FinCube Blockchain Performance Testing  
**Next Review**: Post-execution analysis
