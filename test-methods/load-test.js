import http from "k6/http";
import { check, sleep } from "k6";

// Modified for batch transaction testing
export let options = {
  scenarios: {
    batch_transaction_test: {
      executor: "shared-iterations",
      vus: 1, // Single VU to control the batching logic
      iterations: 40, // 20 POST requests total (20 x 15 = 300 transactions)
      maxDuration: "1h", // Safety timeout
    },
  },
};

export default function () {
  const confirmationDelay = 15; // seconds

  console.log(`Making POST request that triggers 15 transactions...`);

  // Single POST request that creates 15 transactions
  const response = http.post(
    "http://localhost:3000/web3-proxy-service/web3-dao-proxy/place-proposal"
  );

  // Check if the POST request was successful
  const success = check(response, {
    "POST request status 201": (r) => r.status === 201,
  });

  if (success) {
    console.log(`POST request successful - 15 transactions initiated`);
  } else {
    console.log(`POST request failed - status: ${response.status}`);
  }

  // Wait for all 15 transactions to be confirmed before next iteration
  console.log(
    `Waiting ${confirmationDelay} second for transaction confirmation...`
  );
  sleep(confirmationDelay);
}
