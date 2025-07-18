# Test Plan for dApp System Performance

## 1. **Objectives**

- Measure system performance: transaction latency, throughput, resource utilization, and log processing time.
- Evaluate scalability with increasing number of services, event frequency, and dApp features.
- Assess consistency between on-chain events and off-chain state.

---

## 2. **Scope**

- End-to-end transaction processing
- Event handling and logging
- On-chain and off-chain state synchronization

---

## 3. **Test Items**

- dApp API endpoints (transactions, logs, status, etc.)
- On-chain event retrieval endpoints
- Off-chain state endpoints

---

## 4. **Metrics**

- **Transaction Latency:** Time between transaction submission and confirmation.
- **Throughput:** Number of transactions/requests processed per second.
- **Resource Utilization:** CPU, memory, and network usage during tests (collected via system monitoring tools).
- **Log Processing Time:** Time taken to process and store logs/events.
- **Scalability:** System behavior under increasing load (services, event frequency, features).
- **Consistency:** Accuracy of off-chain state compared to on-chain events.

---

## 5. **Test Approach**

### 5.1 **Performance Testing**

- Use k6 scripts to simulate transaction loads and measure latency and throughput.
- Monitor system resources externally (e.g., `htop`, `docker stats`).

### 5.2 **Scalability Testing**

- Gradually increase virtual users and request frequency using k6 staged load.
- Observe system response times and error rates.

### 5.3 **Log Processing Testing**

- Trigger log/event generation and measure the time to process and acknowledge.

### 5.4 **Consistency Testing**

- After transactions/events, compare on-chain records with off-chain state using API checks.

---

## 6. **Test Tools**

- [k6](https://k6.io/) for load and API testing
- System monitoring tools (htop, docker stats, cloud dashboards)
- Custom scripts for consistency checks

---

## 7. **Endpoints to Cover**

- (POST) <http://172.16.231.80:3000/web3-proxy-service/web3-dao-proxy/place-proposal>
- (POST) <http://172.16.231.80:3000/dao-service/proposal-service>
- (GET) <http://172.16.231.80:3000/dao-service/proposal-service>

---

## 8. **Test Execution Notes**

- **Delay Handling:** After each iteration of the POST request to the proxy service (`/web3-proxy-service/web3-dao-proxy/place-proposal`), introduce a 10 second delay before proceeding. This allows sufficient time for the proxy service to execute the transaction and ensures subsequent checks reflect the completed state.

---

## 9. **Reporting**

- Collect and summarize results for each metric.
- Identify bottlenecks, inconsistencies, or security gaps.
- Suggest improvements based on findings.
