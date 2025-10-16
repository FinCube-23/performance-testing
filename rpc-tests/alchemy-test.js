import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

// Custom metrics
const failedRequests = new Counter("failed_requests");
const successRate = new Rate("success_rate");
const requestDuration = new Trend("request_duration");

// Config
const ALCHEMY_URL =
  "https://eth-sepolia.g.alchemy.com/v2/mNVDS9BNNIgmXc5u1oBGNoB9_L2NOo_g";
const fromBlock = "latest";
const toBlock = "latest";
const contractAddress = "0x6e7d437441199bA5cB451921CA58CeAA5E2c293A";

export const options = {
  scenarios: {
    // Basic Load Testing - Respecting 25 req/sec limit
    basic_load_test: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "1m", target: 5 }, // Ramp up to 5 VUs
        { duration: "3m", target: 10 }, // Increase to 10 VUs
        { duration: "5m", target: 15 }, // Max 15 VUs (safe under 25 req/sec)
        { duration: "1m", target: 0 }, // Ramp down
      ],
      startTime: "0s",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<3000", "p(99)<5000"], // Normal thresholds for moderate load
    http_req_failed: ["rate<0.05"], // Less than 5% failures for stable load
    http_reqs: ["count<2500"], // Target 2500 requests
  },
};

export default function () {
  const payload = JSON.stringify({
    jsonrpc: "2.0",
    id: Math.floor(Math.random() * 10000),
    method: "eth_getLogs",
    params: [{ fromBlock, toBlock, address: contractAddress }],
  });

  const params = { headers: { "Content-Type": "application/json" } };
  const start = Date.now();
  const res = http.post(ALCHEMY_URL, payload, params);
  const duration = Date.now() - start;
  requestDuration.add(duration);

  const success = check(res, {
    "status is 200": (r) => r.status === 200,
    "has valid result": (r) => {
      try {
        const jsonResponse = r.json();
        return jsonResponse && jsonResponse.result !== undefined;
      } catch (e) {
        console.error(e);
        return false;
      }
    },
  });

  successRate.add(success);
  if (!success) {
    failedRequests.add(1);
    console.error(`❌ Alchemy Error: ${res.status} - ${res.body}`);
  }

  sleep(Math.random() * 1 + 2); // 2-3 seconds delay for aggressive limit testing
}
