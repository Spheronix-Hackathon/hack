import http from 'k6/http';
import { check, sleep } from 'k6';
import { environments } from '../config/environments.js';

export const options = {
    stages: [
        { duration: '30s', target: 10 },
        { duration: '30s', target: 25 },
        { duration: '30s', target: 50 },
        { duration: '30s', target: 100 },
        { duration: '30s', target: 250 },
        { duration: '30s', target: 0 } // ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<1000'],
        http_req_failed: ['rate<0.02'],
    },
};

const BASE_URL = environments.test.baseUrl;

export default function () {
    // We will simulate browsing activity and basic reads
    let res = http.get(`${BASE_URL}/api/health`);
    check(res, {
        'health status 200': (r) => r.status === 200,
    });
    sleep(Math.random() * 2 + 1); // think time 1-3 seconds

    let payload = JSON.stringify({
        field: 'collegeCode',
        value: `LOAD_TEST_${__VU}_${__ITER}`
    });
    let params = {
        headers: { 'Content-Type': 'application/json' },
    };
    let res2 = http.post(`${BASE_URL}/api/register/check-exists`, payload, params);
    check(res2, {
        'check-exists status is 200': (r) => r.status === 200,
    });
    sleep(Math.random() * 2 + 1);
}
