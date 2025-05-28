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
            @click="$router.push('/createTask')" 
            class="nav-button"
          >
            Создать задачу
          </button>
        </nav>
      </div>
      <div class="user-controls">
        <button @click="logout" class="logout-button">Выйти</button>
        <div class="user-info">
          {{ userLogin }}
        </div>
      </div>
    </header>

    <main class="main-content">
      <h2 class="page-title">Отклики на задачу: {{ taskName }}</h2>
      
      <div v-if="loading" class="loading">Загрузка откликов...</div>
      <div v-else-if="initialLoadError" class="error">{{ initialLoadError }}</div>
      <div v-else-if="responses.length === 0" class="no-responses">
        Нет откликов на эту задачу
      </div>
      
      <div v-else>
        <div class="responses-list">
          <div v-for="executor in responses" :key="executor.user_id" class="executor-card">
            <div class="executor-info">
              <router-link 
                :to="`/userInfo/${executor.user_id || executor.id || 'unknown'}`" 
                class="executor-name"
            >
                {{ executor.name || executor.login }}
            </router-link>
              
              <div class="executor-meta">
                <div class="meta-item">
                    <span class="meta-label">Уровень:</span>
                    <span class="meta-value">
                        {{ executor.level !== undefined && executor.level !== null ? executor.level : 'Не указан' }}
                    </span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Лояльность:</span>
                    <span class="meta-value">
                        {{ executor.loyality !== undefined && executor.loyality !== null ? executor.loyality : 'Не указана' }}
                    </span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">На платформе с:</span>
                  <span class="meta-value">{{ formatDate(executor.date) }}</span>
                </div>
              </div>
              
              <p class="executor-description">{{ executor.description || 'Нет описания' }}</p>
            </div>
            
            <button 
                @click="assignExecutor(executor.user_id)"
                class="assign-button"
                :disabled="isAssigning"
            >
                {{ isAssigning ? 'Назначение...' : 'Назначить' }}
            </button>
          </div>
        </div>
        <div v-if="partialErrors.length > 0" class="partial-errors">
          <h3 class="partial-errors-title">Ошибки при загрузке некоторых исполнителей:</h3>
          <div v-for="(error, index) in partialErrors" :key="index" class="error-message">
            Не удалось загрузить данные для исполнителя ID: {{ error.userId }}. Ошибка: {{ error.message }}
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

export default {
  name: 'TaskResponsesPage',
  data() {
    return {
      loading: false,
      initialLoadError: null,
      partialErrors: [],
      userLogin: '',
      userRole: '',
      taskName: '',
      responses: [],
      isAssigning: false 
    }
  },
  async created() {
    await this.verifyToken();
    await this.fetchTaskName();
    await this.fetchResponses();
  },
  methods: {
    async assignExecutor(executorId) {
      this.isAssigning = true;
      try {
        await this.setExecutor(executorId);
        await this.updateTaskStatus();
        this.$router.push(`/task/${this.$route.params.id}`);
        
      } catch (error) {
        console.error('Ошибка назначения исполнителя:', error);
        alert(`Ошибка: ${error.response?.data?.error || error.message}`);
      } finally {
        this.isAssigning = false;
      }
    },
    
    async setExecutor(executorId) {
      const token = localStorage.getItem('accessToken');
      const response = await axios.put(
        'http://127.0.0.1:8000/task/setExecutor/',
        null,
        {
          params: {
            taskId: this.$route.params.id,
            userId: executorId
          },
          headers: { 
            'Authorization': token 
          }
        }
      );
      return response.data;
    },
    
    async updateTaskStatus() {
      const token = localStorage.getItem('accessToken');
      const currentDate = new Date().toISOString().split('T')[0];
      const response = await axios.put(
        'http://127.0.0.1:8000/task/pushTask/',
        null,
        {
          params: {
            taskID: this.$route.params.id,
            taskStatus: 1,
            modifyDt: currentDate
          },
          headers: { 
            'Authorization': token 
          }
        }
      );
      return response.data;
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
    async fetchTaskName() {
      try {
        const token = localStorage.getItem('accessToken');
        const response = await axios.get(
          `http://127.0.0.1:8000/task/task/?taskId=${this.$route.params.id}`,
          { headers: { 'Authorization': token } }
        );
        
        if (response.data.results.length > 0) {
          this.taskName = response.data.results[0].task_name;
        }
      } catch (error) {
        console.error('Ошибка загрузки названия задачи:', error);
      }
    },
    async fetchResponses() {
        this.loading = true;
        this.initialLoadError = null;
        this.partialErrors = [];
        this.responses = [];
        
        try {
        const token = localStorage.getItem('accessToken');
        const votesResponse = await axios.get(
            `http://127.0.0.1:8000/task/getVotes/?taskId=${this.$route.params.id}`,
            { headers: { 'Authorization': token } }
        );
        
        const executorIds = votesResponse.data.results.map(r => r.executor_id);
        
        for (const id of executorIds) {
            try {
            const response = await axios.get(
                `http://127.0.0.1:8000/administration/getExecutor/?id=${id}`,
                { headers: { 'Authorization': token } }
            );
            
            if (response.data && response.data.length > 0) {
                const executorData = response.data[0];
                if (!executorData.user_id) {
                executorData.user_id = id;
                }
                this.responses.push(executorData);
            }
            } catch (error) {
            console.error(`Ошибка загрузки исполнителя ${id}:`, error);
            this.partialErrors.push({
                userId: id,
                message: error.response?.data?.message || error.message
            });
            }
        }
        
        if (this.responses.length === 0 && executorIds.length > 0) {
            this.initialLoadError = 'Не удалось загрузить ни одного исполнителя';
        }
        
        } catch (error) {
        console.error('Ошибка загрузки списка откликов:', error);
        this.initialLoadError = 'Не удалось загрузить список откликов';
        } finally {
        this.loading = false;
        }
    },
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString('ru-RU');
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

.page-title {
  color: #333;
  text-align: center;
  margin-bottom: 25px;
}

.loading, .initialLoadError, .no-responses {
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

.no-responses {
  color: #666;
  font-style: italic;
}

.responses-list {
  display: grid;
  gap: 20px;
}

.executor-card {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.executor-info {
  flex: 1;
}

.executor-name {
  font-size: 1.2rem;
  color: #2196F3;
  text-decoration: none;
  font-weight: 500;
  margin-bottom: 10px;
  display: inline-block;
}

.executor-name:hover {
  text-decoration: underline;
}

.executor-meta {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
  margin: 15px 0;
}

.meta-item {
  display: flex;
}

.meta-label {
  font-weight: 500;
  margin-right: 5px;
  color: #555;
}

.meta-value {
  color: #333;
}

.executor-description {
  color: #555;
  line-height: 1.5;
  margin-top: 10px;
}

.assign-button {
  padding: 10px 20px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s;
  margin-left: 20px;
  min-width: 120px;
}

.assign-button:hover {
  background-color: #45a049;
}

.partial-errors {
  margin-top: 30px;
  padding: 15px;
  background-color: #ffebee;
  border-radius: 4px;
  border-left: 4px solid #f44336;
}

.partial-errors-title {
  color: #d32f2f;
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
}

.error-message {
  color: #d32f2f;
  margin-bottom: 8px;
  font-size: 14px;
  padding-left: 10px;
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
  
  .executor-card {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .assign-button {
    margin-left: 0;
    margin-top: 15px;
    width: 100%;
  }

  .assign-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
  }
}
</style>