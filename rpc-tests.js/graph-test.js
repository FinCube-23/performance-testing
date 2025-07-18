import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.1/index.js";

// Custom metrics
const failedRequests = new Counter("failed_requests");
const successRate = new Rate("success_rate");
const requestDuration = new Trend("request_duration");

const GRAPHQL_URL =
  "https://api.studio.thegraph.com/query/93678/fincube-proxy-supgraph/0.0.1";
const contractAddress = "0x6e7d437441199bA5cB451921CA58CeAA5E2c293A";
const fromTimestamp = "0";
const toTimestamp = "9999999999";
const limit = 100;

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
  const query = `
    query GetProposalCreateds($limit: Int!) {
      proposalCreateds(first: $limit) {
        id
        transactionHash
      }
    }
  `;

  const payload = JSON.stringify({
    query,
    variables: {
      contract: contractAddress.toLowerCase(),
      from: fromTimestamp,
      to: toTimestamp,
      limit: limit,
    },
  });

  const params = { headers: { "Content-Type": "application/json" } };
  const start = Date.now();
  const res = http.post(GRAPHQL_URL, payload, params);
  const duration = Date.now() - start;
  requestDuration.add(duration);

  const success = check(res, {
    "status is 200": (r) => r.status === 200,
    "no errors": (r) => !r.json().errors,
    "has data": (r) => r.json().data !== undefined,
  });

  successRate.add(success);
  if (!success) {
    failedRequests.add(1);
    console.error(`❌ GraphQL Error: ${res.status} - ${res.body}`);
  }

  sleep(Math.random() * 0.3); // Small jitter to spread load
}
