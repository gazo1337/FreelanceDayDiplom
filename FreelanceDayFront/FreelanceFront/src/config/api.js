const config = {
  baseURL: 'http://127.0.0.1:8000'
};

config.endpoints = {
  admin: `${config.baseURL}/administration/`,
  payments: `${config.baseURL}/adminPayment/`,
  tasks: `${config.baseURL}/task/`
};

export default config;