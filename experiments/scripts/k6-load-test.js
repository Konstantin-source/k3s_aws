import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '10s', target: 10 }, // Ramp-up
    { duration: '90s', target: 15 }, // Stetige Last während Störungsinduktion
    { duration: '20s', target: 0 },  // Ramp-down
  ],
  thresholds: {
    // 95% aller Requests sollten unter 500ms bleiben
    http_req_duration: ['p(95)<500'],
  },
};

const TARGET_URL = __ENV.TARGET_URL || 'http://localhost:8000';

export default function () {
  const res = http.get(`${TARGET_URL}/api/info`);
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'has pod_name': (r) => r.body && r.body.includes('pod_name'),
  });

  sleep(0.5);
}
