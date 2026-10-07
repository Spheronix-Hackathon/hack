import http from 'k6/http';
import { check, sleep } from 'k6';
import { environments } from '../config/environments.js';

export const options = {
    stages: [
        { duration: '10s', target: 10 },
        { duration: '30s', target: 1000 },
        { duration: '30s', target: 1000 },
        { duration: '10s', target: 10 },
    ],
};

const BASE_URL = environments.test.baseUrl;

export default function () {
    let res = http.get(`${BASE_URL}/api/health`);
    check(res, {
        'health status 200': (r) => r.status === 200,
    });
    sleep(1);
}
