import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.1/index.js";

// Custom metrics
const failedRequests = new Counter("failed_requests");
const successRate = new Rate("success_rate");
const requestDuration = new Trend("request_duration");

// Configuration
const BASE_URL = "http://172.16.231.80:3000/dao-service/proposal-service";
const BEARER_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsImVtYWlsIjoiYXNoYWJ1bHJhYWRAZ21haWwuY29tIiwiaWF0IjoxNzU1NTk0MDY1LCJleHAiOjE3NTU2ODA0NjV9._-hcFtooY8Ecm9CLe15j3BSkrNXB8VagkDAVQVyksXQ"; // Replace with actual token

export const options = {
  scenarios: {
    // High Load Testing - Scaling up to 800 VUs
    high_load_test: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "2m", target: 100 }, // Ramp up to 100 VUs
        { duration: "3m", target: 300 }, // Increase to 300 VUs
        { duration: "5m", target: 600 }, // Increase to 600 VUs
        { duration: "5m", target: 800 }, // Max 800 VUs
        { duration: "3m", target: 600 }, // Scale back slightly
        { duration: "2m", target: 0 }, // Ramp down
      ],
      startTime: "0s",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<5000", "p(99)<10000"], // Higher thresholds for high load
    http_req_failed: ["rate<0.10"], // Allow up to 10% failures under extreme load
    http_reqs: ["rate>500"], // Expect high request rate
  },
};

export default function () {
  try {
    const params = {
      headers: {
        Authorization: `Bearer ${BEARER_TOKEN}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    };

    const start = Date.now();
    const response = http.get(BASE_URL, params);
    const duration = Date.now() - start;
    requestDuration.add(duration);

    // Comprehensive checks for GET endpoint
    const success = check(response, {
      "status is 200": (r) => r.status === 200,
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
        `❌ Request Failed: ${response.status} - ${response.body.substring(
          0,
          100
        )}`
      );
    }

    // Log progress for high VU counts
    if (__VU <= 10 && __ITER % 10 === 0) {
      console.log(
        `VU ${__VU}: Iteration ${__ITER}, Status: ${
          response.status
        }, Duration: ${response.timings.duration.toFixed(2)}ms`
      );
    }
  } catch (error) {
    failedRequests.add(1);
    console.error(`❌ Request Error: ${error.message}`);
  }

  // Minimal sleep for high throughput testing
  sleep(Math.random() * 0.2 + 0.1); // 0.1-0.3 seconds
}
