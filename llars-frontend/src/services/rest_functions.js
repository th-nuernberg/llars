import {BASE_URL, TIMEOUT} from "@/config.js";
import axios from 'axios';
import { logI18n } from '@/utils/logI18n';

export async function makePostRequestAsync(path, data) {
  logI18n('log', 'logs.rest.makePostRequest', BASE_URL + path, data);
  return axios.post(BASE_URL + path, data, {
    timeout: TIMEOUT,
  }).catch(error => {
    logI18n('error', 'logs.rest.axiosError', error);
    throw error; // Rethrow, so you can catch it later
  });
}

export function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    router.push('/login');
    // forceUpdate()
    // eventBus.emit("auth-change", false, '')
}
