import http from "k6/http";
import { check, sleep } from "k6";
import { SharedArray } from "k6/data";
import exec from "k6/execution";
import { etherscanTransactionData } from "../datasets/etherscan-transaction-data.js";

// Configuration
const BASE_URL_DAO = "http://172.16.231.80:3000/dao-service/proposal-service";
const BASE_URL_UMS =
  "http://172.16.231.80:3000/user-management-service/api/organizations/onchain-verifications";
const BEARER_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYwNzAxOTIxLCJpYXQiOjE3NjA2MTU1MjEsImp0aSI6ImUxMWE5NjhmYjJlOTQyN2M5ODgyYjQwNDY2M2Y0NzBkIiwidXNlcl9pZCI6IjIifQ.6Fjq-yLCOLKC87NVT-oOVeMe25nJukoHr16nvgUacI0";

// Use SharedArray to share transaction data among VUs efficiently
const transactions = new SharedArray("transactions", function () {
  return etherscanTransactionData.slice(0, 2500); // Use first 2500 transactions from etherscan data
});

// Test configuration
export const options = {
  vus: 10, // 10 virtual users to handle increased load
  iterations: 300, // Total 300 iterations (one per transaction hash)
  duration: "15m", // Increased maximum duration for more transactions
  thresholds: {
    http_req_duration: ["p(95)<5000"], // 95% of requests must complete within 5s
    http_req_failed: ["rate<0.1"], // Error rate should be less than 10%
  },
};

export function setup() {
  console.log(`Starting test with ${transactions.length} transactions`);
  console.log(
    `Using ${options.vus} VUs for ${options.iterations} total iterations`
  );
  console.log(`Each transaction will be sent to BOTH DAO and UMS endpoints`);
  console.log(
    `Total requests: ${options.iterations * 2} (${
      options.iterations
    } per endpoint)`
  );
  return { transactionCount: transactions.length };
}

export default function (data) {
  // Use k6's execution context to get truly unique transaction index
  // exec.scenario.iterationInTest gives us a global iteration counter across all VUs
  const currentTransactionIndex = exec.scenario.iterationInTest;

  // Skip if we've exceeded available transactions
  if (
    currentTransactionIndex >= 2500 ||
    currentTransactionIndex >= transactions.length
  ) {
    console.log(
      `VU ${__VU}: Skipping iteration ${__ITER}, transaction index ${currentTransactionIndex} out of bounds`
    );
    return;
  }

  const transaction = transactions[currentTransactionIndex];
  const trxHash = transaction.trx_hash;

  console.log(
    `VU ${__VU}, Iteration ${__ITER}: Using transaction ${
      currentTransactionIndex + 1
    }/2500: ${trxHash.substring(0, 10)}...`
  );

  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${BEARER_TOKEN}`,
  };

  // Send ALL transactions to DAO Service to ensure all 2500 are saved to PostgreSQL
  const daoPayload = {
    proposal_type: "membership",
    metadata: "string",
    proposer_address: "0x8152f498E91df80bE19a28C83d8596F59FbA80bD",
    trx_hash: trxHash,
  };

  console.log(
    `VU ${__VU}: Testing DAO endpoint with hash ${trxHash.substring(0, 10)}...`
  );

  const daoResponse = http.post(BASE_URL_DAO, JSON.stringify(daoPayload), {
    headers: headers,
    tags: { endpoint: "dao-service" },
  });

  check(daoResponse, {
    "DAO Service - Status is 200 or 201": (r) =>
      r.status === 200 || r.status === 201,
    "DAO Service - Response time < 5s": (r) => r.timings.duration < 5000,
    "DAO Service - No duplicate hash error": (r) =>
      !r.body.includes("Transaction hash already exists"),
  });

  if (daoResponse.status >= 400) {
    console.error(
      `VU ${__VU}: DAO Service error - Status: ${daoResponse.status}, Body: ${daoResponse.body}`
    );
  }

  // Also test UMS endpoint with the same transaction
  const umsPayload = {
    trx_hash: trxHash,
    context: "dummy context",
    proposer_wallet: "0x8152f498E91df80bE19a28C83d8596F59FbA80bD",
    organization_id: 2,
  };

  console.log(
    `VU ${__VU}: Testing UMS endpoint with hash ${trxHash.substring(0, 10)}...`
  );

  const umsResponse = http.post(BASE_URL_UMS, JSON.stringify(umsPayload), {
    headers: headers,
    tags: { endpoint: "ums-service" },
  });

  check(umsResponse, {
    "UMS Service - Status is 200 or 201": (r) =>
      r.status === 200 || r.status === 201,
    "UMS Service - Response time < 5s": (r) => r.timings.duration < 5000,
    "UMS Service - No duplicate hash error": (r) =>
      !r.body.includes("Transaction hash already exists"),
  });

  if (umsResponse.status >= 400) {
    console.error(
      `VU ${__VU}: UMS Service error - Status: ${umsResponse.status}, Body: ${umsResponse.body}`
    );
  }

  // Small delay between requests to avoid overwhelming the server
  sleep(1);
}

export function teardown(data) {
  console.log("Test completed");
  console.log(
    `Processed ${data.transactionCount} transactions across ${options.vus} VUs`
  );
}
