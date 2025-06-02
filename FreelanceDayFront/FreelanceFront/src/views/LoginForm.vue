<template>
  <div class="app-container">
    <header class="header">
      <h1>FreeLanceDay!</h1>
    </header>

    <main class="main-content">
      <div class="welcome-text">Добро пожаловать на биржу!</div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div v-if="error" class="error-message">{{ error }}</div>
        
        <div class="input-group">
          <label>Логин</label>
          <input
            v-model="formData.login"
            type="text"
            placeholder="Введите ваш логин"
            class="input-field"
            required
          >
        </div>
        
        <div class="input-group">
          <label>Пароль</label>
          <input
            v-model="formData.password"
            type="password"
            placeholder="Введите ваш пароль"
            class="input-field"
            required
          >
        </div>
        
        <button 
          type="submit" 
          class="login-button"
          :disabled="loading"
        >
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>
      </form>
      
      <div class="links">
        <router-link to="/register" class="link">Регистрация</router-link>
        <router-link to="/forgot-password" class="link">Забыли пароль?</router-link>
      </div>
    </main>
  </div>
</template>

<script>
import axios from 'axios';
import config from '../config/api.js';

export default {
  data() {
    return {
      formData: {
        login: '',
        password: ''
      }
    }
  },
  methods: {
    async handleLogin() {
      try {
        const params = new URLSearchParams({
          login: this.formData.login,
          password: this.formData.password
        });

        const response = await axios.get(
          `${config.endpoints.admin}login/?${params.toString()}`,
          {
            headers: {
              'Accept': 'application/json',
              'X-CSRFTOKEN': this.getCSRFToken()
            }
          }
        );

        const { access, refresh } = response.data; 

        localStorage.setItem('accessToken', access);
        localStorage.setItem('refreshToken', refresh);

        axios.defaults.headers.common['Authorization'] = `${access}`;

        this.$router.push('/tasks');

      } catch (error) {
        console.error('Ошибка авторизации:', error);
      }
    },
    getCSRFToken() {
      const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
      
      return cookieValue || '';
    }
  }
}</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background-color: white;
  font-family: Arial, sans-serif;
}

.header {
  background-color: #4CAF50;
  color: white;
  padding: 0;
  text-align: left;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.header h1 {
  padding: 20px;
  margin: 0px;
  font-size: 28px;
}

/* Основное содержимое */
.main-content {
  max-width: 400px;
  margin: 40px auto;
  padding: 20px;
  text-align: center;
}

.welcome-text {
  color: #555;
  margin-bottom: 30px;
  font-size: 18px;
}

.login-form {
  background-color: #f9f9f9;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.input-group {
  margin-bottom: 20px;
  text-align: left;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  color: #555;
  font-weight: bold;
}

.input-field {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  box-sizing: border-box;
}

.login-button {
  width: 100%;
  padding: 12px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.login-button:hover {
  background-color: #45a049;
}

.links {
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
}

.link {
  color: #4CAF50;
  text-decoration: none;
  font-size: 14px;
}

.link:hover {
  text-decoration: underline;
}

.error-message {
  color: #ff4444;
  margin-bottom: 15px;
  text-align: center;
}

.login-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>