<template>
  <div class="app-container">
    <header class="header">
      <div class="header-left">
        <h1 class="site-title">FreeLanceDay!</h1>
        <nav class="header-nav">
          <button 
            @click="$router.push('/myProfile')" 
            class="nav-button"
            :class="{ 'active': $route.path === '/myProfile' }"
          >
            Мой профиль
          </button>
          <button 
            @click="$router.push('/myTasks')" 
            class="nav-button"
            :class="{ 'active': $route.path === '/myTasks' }"
          >
            Мои задачи
          </button>
          <button 
            @click="$router.push('/myPayments')" 
            class="nav-button"
            :class="{ 'active': $route.path === '/myPayments' }"
          >
            Мои финансы
          </button>
        </nav>
      </div>
      <div class="user-section">
        <div class="username">
          {{ userLogin }}
        </div>
        <button @click="logout" class="logout-button">Выйти</button>
      </div>
    </header>

    <main class="main-content">
      <div class="task-create-container">
        <h2 class="page-title">Создание новой задачи</h2>
        
        <form @submit.prevent="createTask" class="task-form">
          <div class="form-group">
            <label for="name">Название задачи*</label>
            <input 
              v-model="form.name" 
              type="text" 
              id="name" 
              required
              class="form-input"
              placeholder="Краткое описание задачи"
            >
          </div>
          
          <div class="form-group">
            <label for="description">Описание задачи*</label>
            <textarea 
              v-model="form.description" 
              id="description" 
              rows="5"
              required
              class="form-textarea"
              placeholder="Подробное описание требований к задаче"
            ></textarea>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label for="cost">Стоимость (₽)*</label>
              <input 
                v-model.number="form.cost" 
                type="number" 
                id="cost" 
                min="1"
                required
                class="form-input"
                placeholder="1000"
              >
            </div>
            
            <div class="form-group">
              <label for="complexity">Сложность*</label>
              <select 
                v-model.number="form.complexity" 
                id="complexity" 
                required
                class="form-select"
              >
                <option value="" disabled>Выберите сложность</option>
                <option value="0">Очень легкая</option>
                <option value="1">Легкая</option>
                <option value="2">Средняя</option>
                <option value="3">Сложная</option>
                <option value="4">Очень сложная</option>
              </select>
            </div>
          </div>
          
          <div class="balance-info">
            <span>Доступный баланс: <strong>{{ balance }} ₽</strong></span>
            <span v-if="form.cost > balance" class="error-text">
              (Недостаточно средств)
            </span>
          </div>
          
          <div class="form-actions">
            <button 
              type="button" 
              @click="$router.push('/myTasks')" 
              class="action-button secondary"
            >
              Отмена
            </button>
            <button 
              type="submit" 
              class="action-button primary"
              :disabled="loading || form.cost > balance || !formValid"
            >
              <span v-if="!loading">Создать задачу</span>
              <span v-else>Создание...</span>
            </button>
          </div>
        </form>
        
        <div v-if="error" class="error-message">
          <span class="error-icon">!</span>
          {{ error }}
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import config from '../config/api.js';

export default {
  name: 'CreateTaskPage',
  data() {
    return {
      form: {
        name: '',
        description: '',
        cost: 1000,
        complexity: 2,
        create_dttm: new Date().toISOString().split('T')[0]
      },
      balance: 0,
      loading: false,
      error: null,
      userLogin: '',
      userId: null,
      userRole: ''
    }
  },
  computed: {
    formValid() {
      return this.form.name && 
             this.form.description && 
             this.form.cost > 0 && 
             this.form.complexity !== '';
    }
  },
  async created() {
    await this.verifyToken();
    if (this.userRole !== 'employer') {
      this.$router.push('/myTasks');
      return;
    }
    await this.fetchBalance();
  },
  methods: {
    async verifyToken() {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        this.$router.push('/login');
        return;
      }

      try {
        const decoded = jwtDecode(token);
        this.userLogin = decoded.login;
        this.userRole = decoded.role;
        this.userId = decoded.user_id;
      } catch (error) {
        localStorage.removeItem('accessToken');
        this.$router.push('/login');
      }
    },
    
    async fetchBalance() {
      try {
        const token = localStorage.getItem('accessToken');
        const response = await axios.get(
          `${config.endpoints.payments}getBalance/?id=${this.userId}&role=${this.userRole}`,
          { headers: { 'Authorization': token } }
        );
        this.balance = parseFloat(response.data.balance);
      } catch (error) {
        console.error('Ошибка загрузки баланса:', error);
        this.error = 'Не удалось загрузить информацию о балансе';
      }
    },
    
    async createTask() {
      if (this.form.cost > this.balance) {
        this.error = 'Недостаточно средств на балансе';
        return;
      }

      this.loading = true;
      this.error = null;
      
      try {
        const token = localStorage.getItem('accessToken');

        const taskData = {
          ...this.form,
          initiator: this.userId 
        };

        const taskResponse = await axios.post(
          `${config.endpoints.tasks}createTask/`,
          taskData,  
          { headers: { 'Authorization': token } }
        );
        
        const taskId = taskResponse.data.id;

        await axios.post(
          `${config.endpoints.payments}payment/toTask/`,
          null,
          {
            params: {
              EmployerID: this.userId,
              TaskID: taskId,
              count: this.form.cost,
              date: this.form.create_dttm
            },
            headers: { 
              'Authorization': token 
            }
          }
        );

        this.$router.push('/myTasks');
        
      } catch (error) {
        console.error('Ошибка создания задачи:', error);
        
        if (error.response?.data?.error) {
          this.error = error.response.data.error;
        } else {
          this.error = 'Произошла ошибка при создании задачи';
        }
      } finally {
        this.loading = false;
      }
    },
    
    logout() {
      localStorage.removeItem('accessToken');
      this.$router.push('/login');
    }
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f5f7fa;
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
  gap: 30px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.user-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-info {
  font-size: 14px;
  font-weight: 500;
  order: 1;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 15px;
}

.username {
  font-size: 14px;
  font-weight: 500;
}

.logout-button {
  padding: 6px 12px;
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.logout-button:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

.site-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.header-nav {
  display: flex;
  gap: 10px;
}

.nav-button {
  padding: 8px 16px;
  background-color: transparent;
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.nav-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

.nav-button.active {
  background-color: rgba(255, 255, 255, 0.2);
  border-color: white;
}

.logout-button:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

.user-info {
  font-size: 14px;
  font-weight: 500;
}

.main-content {
  flex: 1;
  padding: 30px;
  background-color: #f5f7fa;
}

.task-create-container {
  max-width: 800px;
  margin: 0 auto;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 30px;
}

.page-title {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 30px;
  font-size: 24px;
  font-weight: 600;
}

.task-form {
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
  font-size: 14px;
}

.form-input, .form-textarea, .form-select {
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.form-input:focus, .form-textarea:focus, .form-select:focus {
  border-color: #4CAF50;
  outline: none;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.form-textarea {
  min-height: 120px;
  resize: vertical;
}

.form-select {
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 16px;
}

.form-row {
  display: flex;
  gap: 20px;
}

.form-row .form-group {
  flex: 1;
}

.balance-info {
  padding: 12px 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
  font-size: 15px;
  color: #333;
}

.balance-info strong {
  font-weight: 600;
}

.error-text {
  color: #f44336;
  margin-left: 10px;
  font-weight: 500;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 20px;
}

.action-button {
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.action-button.primary {
  background-color: #4CAF50;
  color: white;
  border: none;
}

.action-button.primary:hover:not(:disabled) {
  background-color: #45a049;
  transform: translateY(-1px);
}

.action-button.primary:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
  opacity: 0.7;
}

.action-button.secondary {
  background-color: white;
  color: #333;
  border: 1px solid #ddd;
}

.action-button.secondary:hover {
  background-color: #f5f5f5;
}

.error-message {
  margin-top: 20px;
  padding: 15px;
  background-color: #ffebee;
  color: #d32f2f;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.error-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background-color: #d32f2f;
  color: white;
  border-radius: 50%;
  font-weight: bold;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    padding: 15px;
  }
  
  .header-left {
    flex-direction: column;
    gap: 15px;
    width: 100%;
  }
  
  .header-nav {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .nav-button {
    margin: 5px;
  }
  
  .form-row {
    flex-direction: column;
    gap: 15px;
  }
  
  .task-create-container {
    padding: 20px;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .action-button {
    width: 100%;
  }
}
</style>