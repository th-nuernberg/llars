import {BASE_URL} from '@/config';
import axios from 'axios';

export const listSessionsForUser = () => axios.get(`${BASE_URL}/api/comparison/sessions`).then(r => r.data);

export const getSession = (id: number) => axios.get(`${BASE_URL}/api/comparison/session/${id}`).then(r => r.data);

export const sendMessage = (sessionId: number, message: string) =>
  axios.post(`${BASE_URL}/api/comparison/send_message`, {
    session_id: sessionId,
    message: message
  }).then(r => r.data);
