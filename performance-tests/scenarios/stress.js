import http from 'k6/http';
import { check, sleep } from 'k6';
import { environments } from '../config/environments.js';

export const options = {
    stages: [
        { duration: '30s', target: 200 },
        { duration: '30s', target: 400 },
        { duration: '30s', target: 600 },
        { duration: '30s', target: 800 },
        { duration: '30s', target: 1000 },
        { duration: '30s', target: 0 }
    ],
};

const BASE_URL = environments.test.baseUrl;

export default function () {
    let res = http.get(`${BASE_URL}/api/health`);
    check(res, {
        'health status 200': (r) => r.status === 200,
    });
    sleep(1);

    let payload = JSON.stringify({
        field: 'collegeCode',
        value: `STRESS_TEST_${__VU}_${__ITER}`
    });
    let params = {
        headers: { 'Content-Type': 'application/json' },
    };
    let res2 = http.post(`${BASE_URL}/api/register/check-exists`, payload, params);
    check(res2, {
        'check-exists status is 200': (r) => r.status === 200,
    });
    sleep(1);
}
