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
            :class="{ 'class': $route.path === '/myPayments' }"
          >
            Мои финансы
          </button>
        </nav>
      </div>
      <div v-if="userLogin" class="user-controls">
        <div class="user-info">
          {{ userLogin }}
        </div>
        <button @click="logout" class="logout-button">Выйти</button>
      </div>
    </header>

    <main class="main-content">
      <h2 class="tasks-title">Доступные задачи</h2>
      <div class="tasks-list">
        <div v-if="loading" class="loading">Загрузка...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <div v-else-if="paginatedTasks.length === 0" class="no-tasks">
          Нет доступных задач
        </div>
        
        <div v-else v-for="task in paginatedTasks" :key="task.task_id" class="task-card">
          <h3 class="task-name">{{ task.task_name }}</h3>
          <p class="task-desc">{{ task.task_desc }}</p>
          <div class="task-footer">
            <span class="task-cost">{{ task.cost }} ₽</span>
            <div class="task-actions">
              <button 
                @click="$router.push(`/task/${task.task_id}`)" 
                class="task-button details-button"
              >
                Подробнее
              </button>
              
            </div>
          </div>
        </div>
      </div>
      <div v-if="tasks.length > perPage" class="pagination">
        <button 
          @click="currentPage--" 
          :disabled="currentPage === 1"
          class="pagination-button"
        >
          Назад
        </button>
        
        <span class="page-info">
          Страница {{ currentPage }} из {{ totalPages }}
        </span>
        
        <button 
          @click="currentPage++" 
          :disabled="currentPage >= totalPages"
          class="pagination-button"
        >
          Вперед
        </button>
      </div>
    </main>
  </div>
</template>

<script>
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import config from '../config/api.js';

export default {
  name: 'TasksPage',
  data() {
    return {
      tasks: [],
      userData: null,
      loading: false,
      error: null,
      userLogin: '',
      currentPage: 1,
      date: new Date().toISOString().split('T')[0],
      perPage: 6
    }
  },
  computed: {
    
    totalPages() {
      return Math.ceil(this.tasks.length / this.perPage);
    },
    paginatedTasks() {
      const start = (this.currentPage - 1) * this.perPage;
      const end = start + this.perPage;
      return this.tasks.slice(start, end).map(task => ({
        ...task,
        responding: false,
        responded: false
      }));
    }
  },
  async mounted() {
    await this.verifyToken();
    if (this.userData?.role === 'executor') {
      await this.fetchTasks();
    }
  },
  methods: {
    async logout() {
      try {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        delete axios.defaults.headers.common['Authorization'];
        this.$router.push('/login');
      } catch (error) {
        console.error('Ошибка при выходе:', error);
      }
    },
    async verifyToken() {
      const token = localStorage.getItem('accessToken');
      
      if (!token) {
        this.$router.push('/login');
        return;
      }

      try {
        this.userData = jwtDecode(token);
        if (this.userData.role === 'employer') {
          this.$router.push('/myTasks');
          return;
        }
        
        if (this.userData.role !== 'executor') {
          throw new Error('Недостаточно прав');
        }

        this.userLogin = this.userData.login;
        
      } catch (error) {
        localStorage.removeItem('accessToken');
        this.$router.push('/login');
        return;
      }
    },
    async fetchTasks() {
      try {
        const token = localStorage.getItem('accessToken');
        const response = await axios.get(`${config.endpoints.tasks}getTasks/`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        this.tasks = response.data.results;
      } catch (error) {
        this.error = 'Ошибка загрузки задач';
        this.$router.push('/login');
        return;
      }
    },
    async respondToTask(taskId) {
      try {
        const taskIndex = this.tasks.findIndex(t => t.task_id === taskId);
        if (taskIndex !== -1) {
          this.tasks[taskIndex].responding = true;
        }

        const token = localStorage.getItem('accessToken');
        await axios.post(`${config.endpoints.tasks}vote/?taskId=${taskId}&create=${this.date}`, {}, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (taskIndex !== -1) {
          this.tasks[taskIndex].responding = false;
          this.tasks[taskIndex].responded = true;
        }

      } catch (error) {
        console.error('Ошибка при отклике на задачу:', error);
        const taskIndex = this.tasks.findIndex(t => t.task_id === taskId);
        if (taskIndex !== -1) {
          this.tasks[taskIndex].responding = false;
        }
        alert('Не удалось отправить заявку на задачу');
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

.tasks-title {
  color: #333;
  text-align: center;
  margin-bottom: 20px;
}

.tasks-list {
  display: grid;
  gap: 15px;
}

.task-card {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.task-name {
  margin-top: 0;
  color: #2c3e50;
}

.task-desc {
  color: #555;
  margin-bottom: 15px;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-cost {
  font-weight: bold;
  color: #4CAF50;
  font-size: 18px;
}

.task-actions {
  display: flex;
  gap: 10px;
}

.task-button {
  padding: 8px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.details-button {
  background-color: #f0f0f0;
  color: #333;
  border: 1px solid #ddd;
}

.details-button:hover {
  background-color: #e0e0e0;
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

.responded-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  background-color: #e8f5e9;
  color: #2e7d32;
  border-radius: 4px;
  font-size: 14px;
}

.loading, .error, .no-tasks {
  text-align: center;
  padding: 20px;
  color: #555;
}

.error {
  color: #ff4444;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 30px;
  gap: 20px;
}

.pagination-button {
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.pagination-button:hover:not(:disabled) {
  background-color: #45a049;
}

.pagination-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #555;
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
  
  .task-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .task-button, .details-button, .respond-button {
    width: 100%;
  }
}
</style>