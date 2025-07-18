import http from "k6/http";
import { check, sleep } from "k6";

const BEARER_TOKEN = "Your Bearer Token";

// Load Test (steady load, e.g., 15 VUs for 2 minutes)
export let options = {
  scenarios: {
    load_test: {
      executor: "constant-vus",
      vus: 15,
      duration: "2m",
    },
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
