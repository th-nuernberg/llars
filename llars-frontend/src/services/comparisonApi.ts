import {BASE_URL} from '@/config';
import axios from 'axios';

function auth() {
  const api_key = localStorage.getItem('api_key') ?? '';
  return {headers: {Authorization: api_key}};
}

export const listSessionsForUser = () => axios.get(`${BASE_URL}/api/comparison/sessions`, auth()).then(r => r.data);

export const getSession = (id: number) => axios.get(`${BASE_URL}/api/comparison/session/${id}`, auth()).then(r => r.data);

export const sendMessage = (sessionId: number, message: string) =>
  axios.post(`${BASE_URL}/api/comparison/send_message`, {
    session_id: sessionId,
    message: message
  }, auth()).then(r => r.data);
