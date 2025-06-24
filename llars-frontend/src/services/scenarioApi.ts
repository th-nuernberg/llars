import {BASE_URL} from '@/config';
import axios from 'axios';

function auth() {
  const api_key = localStorage.getItem('api_key') ?? '';
  return {headers: {Authorization: api_key}};
}

export const getFunctionTypes = () => axios.get(`${BASE_URL}/api/admin/get_function_types`, auth()).then(r => r.data);
export const getAllUsers = () => axios.get(`${BASE_URL}/api/admin/get_users`, auth()).then(r => r.data);
export const getThreadsOfType = (ftId: number) => axios.get(`${BASE_URL}/api/admin/get_threads_from_function_type/${ftId}`, auth()).then(r => r.data);
export const getAvailableModels = () => axios.get(`${BASE_URL}/api/admin/get_available_models_from_vllm_server`, auth()).then(r => r.data);

export const createScenario = (payload: any) => axios.post(`${BASE_URL}/api/admin/create_scenario`, payload, auth());
export const listScenarios = () => axios.get(`${BASE_URL}/api/admin/scenarios`, auth()).then(r => r.data);
export const getScenarioDetails = (id: number) => axios.get(`${BASE_URL}/api/admin/scenarios/${id}`, auth()).then(r => r.data);
export const deleteScenario = (id: number) => axios.delete(`${BASE_URL}/api/admin/delete_scenario/${id}`, auth());
export const editScenario = (payload: any) => axios.post(`${BASE_URL}/api/admin/edit_scenario`, payload, auth());
