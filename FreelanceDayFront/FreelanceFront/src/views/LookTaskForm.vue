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
          <button 
            v-if="userRole === 'employer'"
            @click="$router.push('/createTask')" 
            class="nav-button"
          >
            Создать задачу
          </button>
          <button 
            v-else
            @click="$router.push('/tasks')" 
            class="nav-button"
          >
            Поиск задач
          </button>
        </nav>
      </div>
      <div class="user-controls">
        <div class="user-info">
          {{ userLogin }}
        </div>
        <button @click="logout" class="logout-button">Выйти</button>
      </div>
    </header>

    <main class="main-content">
      <div v-if="loading" class="loading">Загрузка...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else class="task-detail">
        <div class="task-header">
          <h2 class="task-title">{{ task.task_name }}</h2>
          <div class="task-status" :class="statusClass">
            {{ statusText }}
          </div>
        </div>
        
        <div class="task-meta">
          <div class="meta-item">
            <span class="meta-label">Стоимость:</span>
            <span class="meta-value">{{ task.cost }} ₽</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Сложность:</span>
            <span class="meta-value">{{ complexityText }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Дата создания:</span>
            <span class="meta-value">{{ formattedDate }}</span>
          </div>
          <div class="meta-item" v-if="employerId">
            <span class="meta-label">Заказчик:</span>
            <router-link 
            :to="`/userInfo/${employerId}`" 
            class="user-link"
            @click="handleEmployerClick"
            >
            {{ employerName || 'Загрузка...' }}
            </router-link>
          </div>
          <div v-if="task.executor_id" class="meta-item">
            <span class="meta-label">Исполнитель:</span>
            <router-link 
            :to="`/userInfo/${task.executor_id}`" 
            class="user-link"
            >
            {{ executorName || 'Загрузка...' }}
            </router-link>
          </div>
        </div>
        
        <div class="task-description">
          <h3>Описание задачи</h3>
          <p class="description-text">{{ task.task_desc }}</p>
        </div>
        
        <template v-if="userRole === 'executor'">
      <div v-if="userRole === 'executor' && task.task_status === 'CREATED'" class="task-actions">
    <button 
      v-if="!hasResponded && !responseLoading"
      @click="respondToTask"
      class="action-button respond-button"
    >
      Откликнуться
    </button>
    
    <div v-else-if="hasResponded" class="responded-message">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#4CAF50" viewBox="0 0 16 16">
        <path d="M12.736 3.97a.733.733 0 0 1 1.047 0c.286.289.29.756.01 1.05L7.88 12.01a.733.733 0 0 1-1.065.02L3.217 8.384a.757.757 0 0 1 0-1.06.733.733 0 0 1 1.047 0l3.052 3.093 5.4-6.425a.247.247 0 0 1 .02-.022Z"/>
      </svg>
      <span>Вы уже откликнулись на эту задачу</span>
    </div>
    
    <div v-else class="loading-message">
      Проверка статуса отклика...
    </div>
  </div>

      <button 
        v-else-if="task.task_status === 'IN_PROGRESS' && isCurrentExecutor"
        @click="sendForCompletion"
        class="action-button complete-button"
        :disabled="completionLoading"
    >
        {{ completionLoading ? 'Отправка...' : 'Отправить на завершение' }}
    </button>
    </template>
    <template v-else-if="userRole === 'employer'">
      <button 
        v-if="task.task_status === 'CREATED'"
        @click="viewResponses"
        class="action-button view-button"
      >
        Просмотр откликов
      </button>

      <button 
        v-else-if="task.task_status === 'ON_END' && isTaskOwner"
        @click="completeTask"
        class="action-button finish-button"
        :disabled="completionLoading"
    >
        {{ completionLoading ? 'Завершение...' : 'Завершить задачу' }}
    </button>
    </template>
      </div>
    </main>
  </div>
</template>

<script>
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import config from '../config/api.js';

export default {
  name: 'TaskDetailPage',
  data() {
    return {
      hasResponded: false,
      responseLoading: true,
      task: {},
      loading: false,
      error: null,
      userLogin: '',
      userRole: '',
      responding: false,
      statusMap: {
        'CREATED': { text: 'Создана', class: 'status-created' },
        'IN_PROGRESS': { text: 'Занята', class: 'status-in-progress' },
        'ON_END': { text: 'На завершении', class: 'status-on-end' },
        'ENDED': { text: 'Завершена', class: 'status-ended' }
      },
      employerName: '',
      employerId: null,
      date: new Date().toISOString().split('T')[0],
      executorName: '',
      executorLoading: false,
      completionLoading: false
    }
  },
  computed: {
    statusText() {
      return this.statusMap[this.task.task_status]?.text || this.task.task_status
    },
    statusClass() {
      return this.statusMap[this.task.task_status]?.class || ''
    },
    statusClass() {
      return {
        'status-open': this.task.task_status === 'open',
        'status-in_progress': this.task.task_status === 'in_progress',
        'status-closed': this.task.task_status === 'closed'
      };
    },
    complexityText() {
      const levels = {
        0: 'Очень легкая',
        1: 'Легкая',
        2: 'Средняя',
        3: 'Сложная',
        4: 'Очень сложная'
      };
      return levels[this.task.complexity] || 'Не указана';
    },
    formattedDate() {
      if (!this.task.create_dttm) return '';
      const date = new Date(this.task.create_dttm);
      return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      });
    },
    showEmployerField() {
      return this.employerId !== null || this.loading;
    },
    isCurrentExecutor() {
      return this.task.executor_id === this.userId;
    },
    isTaskOwner() {
      return this.task.task_initiator === this.userId;
    },
    userId() {
      const token = localStorage.getItem('accessToken');
      return token ? jwtDecode(token).user_id : null;
    }
  },
  watch: {
    'task.executor_id': {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.loadExecutorData(newVal);
        }
      }
    }
  },
  async created() {
    await this.verifyToken();
    await this.fetchTask();
    await this.checkIfVoted();
    if (this.task.task_initiator) {
      await this.loadEmployerData(this.task.task_initiator);
    }
  },
  methods: {
    async loadExecutorData(executorId) {
      this.executorLoading = true;
      try {
        const token = localStorage.getItem('accessToken');
        const response = await axios.get(
          `${config.endpoints.admin}getExecutor/?id=${executorId}`,
          { headers: { 'Authorization': token } }
        );
        
        if (response.data?.length > 0) {
          const executor = response.data[0];
          this.executorName = executor.name || executor.login || 'Исполнитель';
        }
      } catch (error) {
        console.error('Ошибка загрузки данных исполнителя:', error);
        this.executorName = 'Неизвестный исполнитель';
      } finally {
        this.executorLoading = false;
      }
    },
    async checkIfVoted() {
      this.responseLoading = true;
      try {
        const token = localStorage.getItem('accessToken');
        const response = await axios.get(
          `${config.endpoints.tasks}ifVote/?taskId=${this.$route.params.id}`,
          { headers: { 'Authorization': token } }
        );
        if (response.data?.status === 'error') {
          this.hasResponded = true;
        } else {
          this.hasResponded = false;
        }
      } catch (error) {
        console.error('Ошибка проверки отклика:', error);
        this.hasResponded = true;
      } finally {
        this.responseLoading = false;
      }
    },
    async loadEmployerData() {
      this.employerId = this.task?.task_initiator
                      || this.task?.employer_id 
                      || this.task?.creator_id 
                      || null;
      if (this.employerId) {
        try {
          const token = localStorage.getItem('accessToken');
          const response = await axios.get(
            `${config.endpoints.admin}getEmployer/?id=${this.employerId}`,
            { headers: { 'Authorization': token } }
          );
          if (response.data?.length > 0) {
            const employer = response.data[0];
            this.employerName = employer.name || employer.login || 'Неизвестный';
          }
        } catch (error) {
          console.error('Ошибка загрузки данных заказчика:', error);
          this.employerName = 'Ошибка загрузки';
        }
      }
    },
    handleEmployerClick(event) {
      this.$router.push(`/userInfo/${this.employerId}`);
    },
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
      } catch (error) {
        localStorage.removeItem('accessToken');
        this.$router.push('/login');
      }
    },
    async fetchTask() {
      this.loading = true;
      try {
        const token = localStorage.getItem('accessToken');
        const response = await axios.get(`${config.endpoints.tasks}task/?taskId=${this.$route.params.id}`, {
          headers: {
            'Authorization': token
          }
        });
        
        if (response.data.results.length > 0) {
          this.task = response.data.results[0];
          await this.checkResponse();
        } else {
          this.error = 'Задача не найдена';
        }
      } catch (error) {
        console.error('Ошибка загрузки задачи:', error);
        this.error = 'Не удалось загрузить данные задачи';
      } finally {
        this.loading = false;
      }
    },
    async checkResponse() {
      try {
        const token = localStorage.getItem('accessToken');
        const response = await axios.get(`${config.endpoints.tasks}checkResponse/?taskId=${this.$route.params.id}`, {
          headers: {
            'Authorization': token
          }
        });
        this.responded = response.data.hasResponded;
      } catch (error) {
        console.error('Ошибка проверки отклика:', error);
      }
    },
    async respondToTask() {
      this.responding = true;
      try {
        const token = localStorage.getItem('accessToken');
        await axios.post(`${config.endpoints.tasks}vote/?taskId=${this.$route.params.id}&create=${this.date}`, {}, {
          headers: {
            'Authorization': token
          }
        });
        this.responded = true;
        this.hasResponded = true;
      } catch (error) {
        console.error('Ошибка отклика на задачу:', error);
        alert('Не удалось отправить отклик');
      } finally {
        this.responding = false;
      }
    },
    async closeTask() {
      try {
        const token = localStorage.getItem('accessToken');
        await axios.post(`${config.endpoints.tasks}${this.$route.params.id}/close/`, {}, {
          headers: {
            'Authorization': token
          }
        });
        this.task.task_status = 'closed';
      } catch (error) {
        console.error('Ошибка закрытия задачи:', error);
        alert('Не удалось закрыть задачу');
      }
    },
    editTask() {
      this.$router.push(`/editTask/${this.$route.params.id}`);
    },
    logout() {
      localStorage.removeItem('accessToken');
      this.$router.push('/login');
    },
     async sendForCompletion() {
      this.completionLoading = true;
      try {
        const token = localStorage.getItem('accessToken');
        const currentDate = new Date().toISOString().split('T')[0]; 
        
        const response = await axios.put(
          `${config.endpoints.tasks}pushTask/`,
          null,
          {
            params: {
              taskID: this.task.task_id,
              taskStatus: 2, 
              modifyDt: currentDate
            },
            headers: { 
              'Authorization': token 
            }
          }
        );
        this.task.task_status = 'ON_END';
        alert('Задача отправлена на завершение!');
        
      } catch (error) {
        console.error('Ошибка отправки на завершение:', error);
        
        let errorMessage = 'Не удалось отправить задачу на завершение';
        if (error.response?.data?.error) {
          errorMessage += `: ${error.response.data.error}`;
        }
        
        alert(errorMessage);
      } finally {
        this.completionLoading = false;
      }
    },
    async completeTask() {
      if (!confirm('Вы уверены, что хотите завершить задачу и перевести оплату исполнителю?')) {
        return;
      }

      this.completionLoading = true;
      try {
        const token = localStorage.getItem('accessToken');
        const currentDate = new Date().toISOString().split('T')[0];
        await axios.put(
          `${config.endpoints.tasks}pushTask/`,
          null,
          {
            params: {
              taskID: this.task.task_id,
              taskStatus: 3, 
              modifyDt: currentDate
            },
            headers: { 
              'Authorization': token 
            }
          }
        );
        await axios.post(
          `${config.endpoints.payments}payment/toExecutor/`,
          null,
          {
            params: {
              ExecutorID: this.task.executor_id,
              TaskID: this.task.task_id,
              count: this.task.cost, 
              date: currentDate
            },
            headers: { 
              'Authorization': token 
            }
          }
        );
        this.task.task_status = 'ENDED';
        alert('Задача успешно завершена и оплата переведена исполнителю!');
        
      } catch (error) {
        console.error('Ошибка завершения задачи:', error);
        
        let errorMessage = 'Не удалось завершить задачу';
        if (error.response?.data?.error) {
          errorMessage += `: ${error.response.data.error}`;
        }
        
        alert(errorMessage);
      } finally {
        this.completionLoading = false;
      }
    },
    viewResponses() {
      this.$router.push(`/task/${this.task.task_id}/responses`);
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
  gap: 30px;
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
  transition: all 0.3s ease;
}

.nav-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

.nav-button.active {
  background-color: rgba(255, 255, 255, 0.2);
  border-color: white;
  font-weight: bold;
}

.user-controls {
  display: flex;
  align-items: center;
  gap: 15px;
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

.user-info {
  font-size: 14px;
  font-weight: 500;
}

.main-content {
  max-width: 800px;
  margin: 20px auto;
  padding: 0 20px;
}

.task-detail {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 25px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.task-title {
  margin: 0;
  color: #2c3e50;
  font-size: 24px;
}

.task-status {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  color: black;
}

.status-created {
  background-color: #2196F3;
}

.status-in-progress {
  background-color: #FF9800; 
}

.status-on-end {
  background-color: #9C27B0;
}

.status-ended {
  background-color: #4CAF50; 
}

.task-meta {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 25px;
}

.meta-item {
  display: flex;
  flex-direction: column;
}

.meta-label {
  font-size: 14px;
  color: #666;
}

.meta-value {
  font-weight: 500;
  color: #333;
}

.task-description {
  margin-bottom: 30px;
}

.task-description h3 {
  color: #333;
  margin-bottom: 10px;
}

.description-text {
  color: #444; 
  line-height: 1.6;
  white-space: pre-line;
}

.task-actions {
  display: flex;
  gap: 15px;
  margin-top: 30px;
}

.action-button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.respond-button {
  background-color: #4CAF50;
  color: white;
}

.respond-button:hover:not(:disabled) {
  background-color: #45a049;
}

.respond-button:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

.close-button {
  background-color: #f44336;
  color: white;
}

.close-button:hover {
  background-color: #d32f2f;
}

.edit-button {
  background-color: #2196F3;
  color: white;
}

.edit-button:hover {
  background-color: #1976D2;
}

.responded-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 20px;
  padding: 12px;
  background-color: #e8f5e9;
  color: #2e7d32;
  border-radius: 4px;
  font-size: 16px;
}

.loading, .error {
  text-align: center;
  padding: 40px;
  font-size: 18px;
}

.error {
  color: #f44336;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    height: auto;
    padding: 10px;
  }
  
  .header-left {
    flex-direction: column;
    gap: 10px;
    width: 100%;
  }
  
  .header-nav {
    flex-wrap: wrap;
    justify-content: center;
    margin: 10px 0;
  }
  
  .nav-button {
    margin: 5px;
    flex: 1 0 auto;
    min-width: 120px;
  }
  
  .user-controls {
    margin-top: 10px;
    width: 100%;
    justify-content: center;
  }
  
  .task-meta {
    grid-template-columns: 1fr;
  }
  
  .task-actions {
    flex-direction: column;
  }
  
  .action-button {
    width: 100%;
  }
}
.user-link {
  color: #2196F3;
  text-decoration: none;
  transition: color 0.3s;
}

.user-link:hover {
  text-decoration: underline;
  color: #0d8bf2;
}

.meta-item {
  margin-bottom: 12px;
}

.meta-label {
  font-weight: 500;
  margin-right: 8px;
  color: #555;
}

.complete-button {
  background-color: #FF9800;
  color: white;
}

.complete-button:hover:not(:disabled) {
  background-color: #F57C00;
}

.complete-button:disabled {
  background-color: #FFE0B2;
  cursor: not-allowed;
}

.view-button {
  background-color: #2196F3;
  color: white;
}

.view-button:hover {
  background-color: #1976D2;
}

.finish-button {
  background-color: #4CAF50;
  color: white;
}

.finish-button:hover:not(:disabled) {
  background-color: #388E3C;
}

.finish-button:disabled {
  background-color: #C8E6C9;
  cursor: not-allowed;
}

.responded-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background-color: #e8f5e9;
  color: #2e7d32;
  border-radius: 4px;
}

.loading-message {
  padding: 10px;
  color: #666;
  font-style: italic;
}

.action-button {
  padding: 10px 20px;
}

.user-link {
  color: #2196F3;
  text-decoration: none;
  transition: color 0.3s;
}

.user-link:hover {
  text-decoration: underline;
  color: #0d8bf2;
}
</style>