import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";
import { transactionData } from "./transaction-data.js";

// Custom metrics
const failedRequests = new Counter("failed_requests");
const successRate = new Rate("success_rate");
const requestDuration = new Trend("request_duration");

// Configuration
const BASE_URL = "http://172.16.231.80:3000/dao-service/proposal-service";
const BEARER_TOKEN = "BEARER_TOKEN FROM THE FRONTEND"; // Replace with actual token

export const options = {
  scenarios: {
    // POST Load Testing
    post_load_test: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "1m", target: 10 }, // Ramp up to 10 VUs
        { duration: "3m", target: 25 }, // Increase to 25 VUs
        { duration: "5m", target: 50 }, // Max 50 VUs for POST requests
        { duration: "1m", target: 0 }, // Ramp down
      ],
      startTime: "0s",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<3000", "p(99)<5000"], // POST requests typically slower
    http_req_failed: ["rate<0.05"], // Less than 5% failures
    http_reqs: ["count<2000"], // Reasonable limit for POST operations
  },
};

export default function () {
  try {
    // Get transaction data from imported array (300 real transactions from CSV)
    const transactionIndex = (__VU * 1000 + __ITER) % transactionData.length;
    const currentTransaction = transactionData[transactionIndex];

    const payload = {
      proposal_type: "membership",
      metadata: "string",
      proposer_address: currentTransaction.proposedWallet,
      trx_hash: currentTransaction.trx_hash,
    };

    const params = {
      headers: {
        Authorization: `Bearer ${BEARER_TOKEN}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    };

    const start = Date.now();
    const response = http.post(BASE_URL, JSON.stringify(payload), params);
    const duration = Date.now() - start;
    requestDuration.add(duration);

    // Comprehensive checks for POST endpoint
    const success = check(response, {
      "status is 200 or 201": (r) => r.status === 200 || r.status === 201,
      "response time < 5000ms": (r) => r.timings.duration < 5000,
      "has response body": (r) => r.body && r.body.length > 0,
      "content type is JSON": (r) =>
        r.headers["Content-Type"] &&
        r.headers["Content-Type"].includes("application/json"),
      "no server errors": (r) => r.status < 500,
    });

    successRate.add(success);

    if (!success) {
      failedRequests.add(1);
      console.error(
        `❌ POST Request Failed: ${response.status} - ${response.body.substring(
          0,
          200
        )}`
      );
    }

    // Log progress for monitoring
    if (__VU <= 5 && __ITER % 5 === 0) {
      console.log(
        `VU ${__VU}: Iteration ${__ITER}, Status: ${
          response.status
        }, TrxHash: ${currentTransaction.trx_hash.substring(
          0,
          10
        )}..., ProposedWallet: ${currentTransaction.proposedWallet.substring(
          0,
          10
        )}...`
      );
    }
  } catch (error) {
    failedRequests.add(1);
    console.error(`❌ POST Request Error: ${error.message}`);
  }

  // Sleep between requests to avoid overwhelming the server
  sleep(Math.random() * 0.5 + 0.3); // 0.3-0.8 seconds
}
