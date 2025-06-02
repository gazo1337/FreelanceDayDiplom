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
      <h2 class="tasks-title">Мои задачи</h2>
      
      <div class="tasks-list">
        <div v-if="loading" class="loading">Загрузка...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <div v-else-if="tasks.length === 0" class="no-tasks">
          Нет активных задач
        </div>
        
        <div v-else v-for="task in paginatedTasks" :key="task.task_id" class="task-card">
          <h3 class="task-name">{{ task.task_name }}</h3>
          <p class="task-desc">{{ task.task_desc }}</p>
          <div class="task-footer">
            <span class="task-cost">{{ task.cost }} ₽</span>
            <router-link 
              :to="`/task/${task.task_id}`" 
              class="task-button details-button"
            >
              Подробнее
            </router-link>
          </div>
        </div>
      </div>

      <!-- Пагинация -->
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
  name: 'MyTasksPage',
  data() {
    return {
      tasks: [],
      loading: false,
      error: null,
      userLogin: '',
      userRole: '',
      currentPage: 1,
      perPage: 5
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.tasks.length / this.perPage);
    },
    paginatedTasks() {
      const start = (this.currentPage - 1) * this.perPage;
      const end = start + this.perPage;
      return this.tasks.slice(start, end);
    }
  },
  async created() {
    await this.verifyToken();
    await this.fetchTasks();
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
      } catch (error) {
        localStorage.removeItem('accessToken');
        this.$router.push('/login');
      }
    },
    async fetchTasks() {
      this.loading = true;
      this.error = null;
      
      try {
        const token = localStorage.getItem('accessToken');
        const endpoint = this.userRole === 'executor' 
          ? 'getExTask' 
          : 'getEmpTask';
        
        const response = await axios.get(
          `${config.endpoints.tasks}${endpoint}/`, 
          {
            headers: { 'Authorization': token }
          }
        );
        
        this.tasks = response.data.results || [];
      } catch (error) {
        console.error('Ошибка загрузки задач:', error);
        this.error = error.response?.data?.error || 'Не удалось загрузить задачи';
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

.site-title {
  margin: 0;
  font-size: 1.5rem;
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
  font-size: 1.2rem;
}

.task-desc {
  color: #555;
  margin-bottom: 15px;
  line-height: 1.5;
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

.task-button {
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s;
}

.details-button {
  background-color: #2196F3;
  color: white;
  border: none;
}

.details-button:hover {
  background-color: #1976D2;
}

.loading, .error, .no-tasks {
  text-align: center;
  padding: 40px;
  font-size: 18px;
}

.loading {
  color: #666;
}

.error {
  color: #f44336;
}

.no-tasks {
  color: #666;
  font-style: italic;
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
  
  .task-card {
    padding: 15px;
  }
  
  .pagination {
    flex-direction: column;
    gap: 10px;
  }
}
</style>