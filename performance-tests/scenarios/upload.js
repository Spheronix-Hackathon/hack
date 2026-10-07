import http from 'k6/http';
import { check, sleep } from 'k6';
import { environments } from '../config/environments.js';
import { FormData } from 'https://jslib.k6.io/formdata/0.0.2/index.js';

const smallExcel = open('../data/upload-small.xlsx', 'b');
const mediumExcel = open('../data/upload-medium.xlsx', 'b');

export const options = {
    scenarios: {
        small_upload: {
            executor: 'constant-vus',
            vus: 5,
            duration: '10s',
            exec: 'uploadSmall',
        },
        medium_upload: {
            executor: 'constant-vus',
            vus: 5,
            duration: '10s',
            exec: 'uploadMedium',
            startTime: '10s'
        }
    }
};

const BASE_URL = environments.test.baseUrl;
const JWT = __ENV.K6_JWT;

export function uploadSmall() {
    let fd = new FormData();
    fd.append('file', http.file(smallExcel, 'upload-small.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'));

    let res = http.post(`${BASE_URL}/api/dashboard/upload-data`, fd.body(), {
        headers: { 
            'Content-Type': 'multipart/form-data; boundary=' + fd.boundary,
            'Authorization': `Bearer ${JWT}`
        },
    });
    
    check(res, {
        'status is 200': (r) => r.status === 200,
    });
    sleep(1);
}

export function uploadMedium() {
    let fd = new FormData();
    fd.append('file', http.file(mediumExcel, 'upload-medium.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'));

    let res = http.post(`${BASE_URL}/api/dashboard/upload-data`, fd.body(), {
        headers: { 
            'Content-Type': 'multipart/form-data; boundary=' + fd.boundary,
            'Authorization': `Bearer ${JWT}`
        },
    });
    
    check(res, {
        'status is 200': (r) => r.status === 200,
    });
    sleep(1);
}
