// Copyright (C) 2025 IBM Corp.
// SPDX-License-Identifier: Apache-2.0

import axios from 'axios';

axios.defaults.withCredentials = true;

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});
