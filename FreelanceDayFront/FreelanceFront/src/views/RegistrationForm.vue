<template>
  <div class="app-container">
    <header class="header">
      <div class="header-left">
        <h1 class="site-title">FreeLanceDay!</h1>
      </div>
      <div class="user-controls">
        <button @click="$router.push('/login')" class="login-button">Войти</button>
      </div>
    </header>

    <main class="main-content">
      <div class="auth-container">
        <h2 class="auth-title">Регистрация</h2>
        
        <form @submit.prevent="register" class="auth-form">
          <div class="form-group">
            <label for="login">Логин*</label>
            <input 
              v-model="form.login" 
              type="text" 
              id="login" 
              required
              class="form-input"
            >
          </div>
          
          <div class="form-group">
            <label for="password">Пароль*</label>
            <input 
              v-model="form.password" 
              type="password" 
              id="password" 
              required
              minlength="8"
              class="form-input"
            >
          </div>
          <div class="form-group role-switch">
            <label>Вы регистрируетесь как:</label>
            <div class="switch-container">
              <button 
                type="button"
                @click="form.role = 'employer'"
                :class="{ 'active': form.role === 'employer' }"
                class="role-button"
              >
                Заказчик
              </button>
              <button 
                type="button"
                @click="form.role = 'executor'"
                :class="{ 'active': form.role === 'executor' }"
                class="role-button"
              >
                Исполнитель
              </button>
            </div>
          </div>
          <template v-if="form.role === 'employer'">
            <div class="form-group">
              <label for="name">Имя*</label>
              <input 
                v-model="form.name" 
                type="text" 
                id="name" 
                required
                class="form-input"
              >
            </div>
            
            <div class="form-group">
              <label for="organization">Организация</label>
              <input 
                v-model="form.organization" 
                type="text" 
                id="organization" 
                class="form-input"
              >
            </div>
            
            <div class="form-group">
              <label for="description">Описание деятельности</label>
              <textarea 
                v-model="form.description" 
                id="description" 
                rows="4"
                class="form-textarea"
              ></textarea>
            </div>
          </template>
          <template v-else>
            <div class="form-group">
              <label for="name">Имя*</label>
              <input 
                v-model="form.name" 
                type="text" 
                id="name" 
                required
                class="form-input"
              >
            </div>
            
            <div class="form-group">
              <label for="description">О себе</label>
              <textarea 
                v-model="form.description" 
                id="description" 
                rows="4"
                class="form-textarea"
              ></textarea>
            </div>
          </template>
          
          <div class="form-footer">
            <button 
              type="button" 
              @click="$router.push('/login')" 
              class="auth-button secondary"
            >
              На главную
            </button>
            <button 
              type="submit" 
              class="auth-button primary"
              :disabled="loading"
            >
              <span v-if="!loading">Зарегистрироваться</span>
              <span v-else>Регистрация...</span>
            </button>
          </div>
        </form>
        <div v-if="error" class="error-message">{{ error }}</div>
        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
          <router-link to="/login" class="login-link">Войти сейчас</router-link>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import axios from 'axios'; 
import config from '../config/api.js';

export default {
  name: 'RegisterPage',
  data() {
    return {
      form: {
        login: '',
        password: '',
        role: 'employer',
        name: '',
        organization: '',
        description: '',
        date: new Date().toISOString().split('T')[0],
      },
      loading: false,
      error: null,
      successMessage: '',
      userId: null
    }
  },
  methods: {
    async register() {
      if (!this.form.login || !this.form.password || !this.form.name) {
        this.error = 'Пожалуйста, заполните все обязательные поля';
        return;
      }
      
      if (this.form.password.length < 8) {
        this.error = 'Пароль должен содержать минимум 8 символов';
        return;
      }

      this.loading = true;
      this.error = null;
      
      try {
        const requestData = {
          login: this.form.login,
          password: this.form.password,
          role: this.form.role,
          username: this.form.name,
          description: this.form.description,
          date: this.form.date
        };
        if (this.form.role === 'employer') {
          requestData.organization = this.form.organization || 'Индивидуальный предприниматель';
        }
        const response = await axios.post(`${config.endpoints.admin}register/`, requestData);
        this.successMessage = 'Регистрация прошла успешно!';
        setTimeout(() => {
          this.$router.push('/login');
        }, 3000);
        this.successMessage = 'Регистрация прошла успешно!';
        this.userId = response.data.id;

        await this.createVirtualCard(this.userId, this.form.role, this.form.date);
        this.form = {
          login: '',
          password: '',
          role: 'employer',
          name: '',
          organization: '',
          description: '',
          date: new Date().toISOString().split('T')[0]
        };
        setTimeout(() => {
          this.$router.push('/login');
        }, 3000);
        
      } catch (error) {
        console.error('Ошибка регистрации:', error);
        if (error.response) {
          if (error.response.status === 401) {
            this.error = 'Пользователь с таким логином уже существует';
          } else {
            this.error = error.response.data.error || 'Произошла ошибка при регистрации';
          }
        } else if (error.request) {
          this.error = 'Не удалось соединиться с сервером';
        } else {
          this.error = 'Произошла ошибка при отправке запроса';
        }
      } finally {
        this.loading = false;
      }
    },
    async createVirtualCard(ownerId, role, date) {
      try {
        const cardData = {
          owner: this.userId,
          role: this.form.role,
          modify_dttm: this.form.date
        };

        const response = await axios.post(
          `${config.endpoints.payments}createCard/`,
          cardData
        );

        console.log('Виртуальная карта создана:', response.data);
      } catch (error) {
        console.error('Ошибка создания виртуальной карты:', error);
        this.error = 'Регистрация прошла успешно, но не удалось создать платежный аккаунт. Обратитесь в поддержку.';
      }
    }
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background-color: white;
  font-family: Arial, sans-serif;
}

.header {
  background-color: #4CAF50;
  color: white;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
}

.site-title {
  margin: 0;
  font-size: 1.5rem;
}

.user-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.login-button {
  padding: 6px 12px;
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.login-button:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

.main-content {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 60px);
  padding: 20px;
}

.auth-container {
  width: 100%;
  max-width: 500px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 30px;
}

.auth-title {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 25px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 500;
  color: #555;
}

.form-input, .form-textarea {
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.form-input:focus, .form-textarea:focus {
  border-color: #4CAF50;
  outline: none;
}

.form-textarea {
  resize: vertical;
  min-height: 100px;
}

.role-switch {
  margin: 15px 0;
}

.switch-container {
  display: flex;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #ddd;
}

.role-button {
  flex: 1;
  padding: 10px;
  background-color: #f5f5f5;
  border: none;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s;
}

.role-button.active {
  background-color: #4CAF50;
  color: white;
}

.form-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  gap: 15px;
}

.auth-button {
  flex: 1;
  padding: 12px;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.auth-button.primary {
  background-color: #4CAF50;
  color: white;
  border: none;
}

.auth-button.primary:hover:not(:disabled) {
  background-color: #45a049;
}

.auth-button.primary:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

.auth-button.secondary {
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.auth-button.secondary:hover {
  background-color: #e0e0e0;
}

.error-message {
  margin-top: 20px;
  padding: 10px 15px;
  background-color: #ffebee;
  color: #d32f2f;
  border-radius: 4px;
  text-align: center;
}

@media (max-width: 600px) {
  .auth-container {
    padding: 20px;
  }
  
  .form-footer {
    flex-direction: column;
  }
}

.success-message {
  margin-top: 20px;
  padding: 15px;
  background-color: #e8f5e9;
  color: #2e7d32;
  border-radius: 4px;
  text-align: center;
}

.login-link {
  display: block;
  margin-top: 10px;
  color: #1b5e20;
  font-weight: bold;
  text-decoration: none;
}

.login-link:hover {
  text-decoration: underline;
}

.error-message {
  margin-top: 20px;
  padding: 15px;
  background-color: #ffebee;
  color: #d32f2f;
  border-radius: 4px;
  text-align: center;
}
</style>