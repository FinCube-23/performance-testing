import http from "k6/http";
import { check, sleep } from "k6";

const BEARER_TOKEN = "Your Bearer Token";

// Stress Test (ramp up to high VUs, sustain, then ramp down)
export let options = {
  scenarios: {
    stress_test: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "2m", target: 20 }, // ramp to 20 VUs
        { duration: "3m", target: 40 }, // ramp to 40 VUs
        { duration: "2m", target: 60 }, // ramp to 60 VUs
        { duration: "2m", target: 0 }, // ramp down to 0 VUs
      ],
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<4000"],
    http_req_failed: ["rate<0.02"],
  },
};

function getAuthHeaders() {
  return {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${BEARER_TOKEN}`,
    },
  };
}

export default function () {
  const payload = JSON.stringify("Your payload as an object");

  // query example
  const query = http.get(
    "Your query endpoint URL"
    // payload and auth headers if required
    // payload,
    // getAuthHeaders()
  );

  check(query, {
    "query status 200": (r) => r.status === 200,
  });

  // post example
  const post = http.post(
    "Your post endpoint URL"
    // payload and auth headers if required
    // payload,
    // getAuthHeaders());
  );

  check(post, {
    "post status 200": (r) => r.status === 200,
  });

  // sleeper after each iteration
  sleep(1);
}
