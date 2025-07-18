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
    constant_load: {
      executor: "constant-arrival-rate",
      rate: 10, // 10 requests per second
      timeUnit: "1s",
      duration: "200s", // 10 * 200 = 2000 requests
      preAllocatedVUs: 20,
      maxVUs: 50,
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<1000"],
    success_rate: ["rate>0.95"],
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
    "has valid result": (r) => r.json().result !== undefined,
  });

  successRate.add(success);
  if (!success) {
    failedRequests.add(1);
    console.error(`❌ Alchemy Error: ${res.status} - ${res.body}`);
  }

  sleep(Math.random() * 0.5); // Optional: add jitter
}
