import {BASE_URL, TIMEOUT} from "@/config.js";
import axios from 'axios';

export async function makePostRequestAsync(path, data) {
  console.log("makePostRequestAsync", BASE_URL + path, data);
  return axios.post(BASE_URL + path, data, {
    timeout: TIMEOUT,
  }).catch(error => {
    console.error("Axios error:", error);
    throw error; // Rethrow, so you can catch it later
  });
}