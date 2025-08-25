import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

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
    // Basic Load Testing - Same ramping as Alchemy test
    basic_load_test: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "1m", target: 5 }, // Ramp up to 5 VUs
        { duration: "3m", target: 10 }, // Increase to 10 VUs
        { duration: "5m", target: 15 }, // Max 15 VUs
        { duration: "1m", target: 0 }, // Ramp down
      ],
      startTime: "0s",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<2000", "p(99)<3000"], // More lenient for GraphQL calls
    http_req_failed: ["rate<0.05"], // Less than 5% failures
    http_reqs: ["count<800"], // Adjusted for 15 VUs over 10 minutes
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

  // Conservative sleep to prevent rate limiting on The Graph API
  // Longer intervals ensure stable performance testing
  sleep(Math.random() * 1 + 1.5); // 1.5-2.5 seconds between requests
}
