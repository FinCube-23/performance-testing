import http from "k6/http";
import { check, sleep } from "k6";

const BEARER_TOKEN = "Your Bearer Token";

// Spike Test (sudden increase/decrease in VUs)
export let options = {
  scenarios: {
    spike_test: {
      executor: "ramping-arrival-rate",
      startRate: 5,
      preAllocatedVUs: 50,
      stages: [
        { target: 5, duration: "30s" }, // low traffic
        { target: 50, duration: "10s" }, // spike to high
        { target: 5, duration: "1m" }, // return to baseline
      ],
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<3500"],
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
    "Your query endpoint URL",
    // payload and auth headers if required
    payload,
    getAuthHeaders()
  );

  check(query, {
    "query status 200": (r) => r.status === 200,
  });

  // post example
  const post = http.post(
    "Your post endpoint URL",
    // payload and auth headers if required
    payload,
    getAuthHeaders()
  );

  check(post, {
    "post status 200": (r) => r.status === 200,
  });

  // sleeper after each iteration
  sleep(1);
}
