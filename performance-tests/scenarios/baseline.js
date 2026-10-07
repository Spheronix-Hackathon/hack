import http from 'k6/http';
import { check, sleep } from 'k6';
import { environments } from '../config/environments.js';

export const options = {
    vus: 5,
    duration: '30s',
    thresholds: {
        http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
        http_req_failed: ['rate<0.01'], // <1% errors
    },
};

const BASE_URL = environments.test.baseUrl;

export default function () {
    // 1. Health check
    let res = http.get(`${BASE_URL}/api/health`);
    check(res, {
        'health check status is 200': (r) => r.status === 200,
    });
    sleep(1);

    // 2. Check exists API (simulate pre-registration check)
    let payload = JSON.stringify({
        field: 'collegeCode',
        value: `CCODE_TEST_${__VU}`
    });
    let params = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    let res2 = http.post(`${BASE_URL}/api/register/check-exists`, payload, params);
    check(res2, {
        'check-exists status is 200': (r) => r.status === 200,
    });
    sleep(1);
}
