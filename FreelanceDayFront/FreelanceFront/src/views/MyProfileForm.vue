<template>
  <div class="app-container">
    <header class="header">
      <div class="header-left">
        <h1 class="site-title">FreeLanceDay!</h1>
        <nav class="header-nav">
          <button 
            @click="$router.push('/myTasks')" 
            class="nav-button"
          >
            Мои задачи
          </button>
          <button 
            @click="$router.push('/myPayments')" 
            class="nav-button"
          >
            Мои финансы
          </button>
          <button 
            v-if="userRole === 'executor'"
            @click="$router.push('/tasks')" 
            class="nav-button"
          >
            Поиск задач
          </button>
          <button 
            v-if="userRole === 'employer'"
            @click="$router.push('/createTask')" 
            class="nav-button"
          >
            Создать задачу
          </button>
        </nav>
      </div>
      <div class="user-controls">
        <div class="user-info">
          {{ userData.login }}
        </div>
        <button @click="logout" class="logout-button">Выйти</button>
      </div>
    </header>

    <main class="main-content">
      <div class="profile-container">
        <div class="profile-header">
          <h2 class="profile-title">Мой профиль</h2>
          <span class="profile-date">На платформе с {{ formatDate(userData.date) }}</span>
        </div>

        <div class="profile-card">
          <div class="profile-info">
            <div class="info-section">
              <h3 class="section-title">Основная информация</h3>
              <div class="info-row">
                <span class="info-label">Имя:</span>
                <span class="info-value">{{ userData.name }}</span>
              </div>
              
              <div v-if="userRole === 'employer'" class="info-row">
                <span class="info-label">Организация:</span>
                <span class="info-value">{{ userData.oranization || 'Не указано' }}</span>
              </div>
              
              <div v-if="userRole === 'executor'" class="info-row">
                <span class="info-label">Уровень:</span>
                <span class="info-value">{{ userData.level !== null && userData.level !== undefined ? userData.level : 'Не указан' }}</span>
              </div>
              
              <div v-if="userRole === 'executor'" class="info-row">
                <span class="info-label">Рейтинг лояльности:</span>
                <span class="info-value">{{ userData.loyality !== null && userData.loyality !== undefined ? userData.loyality : 'Не указан' }}</span>
              </div>
            </div>

            <div class="info-section">
              <h3 class="section-title">О себе</h3>
              <div class="description">
                {{ userData.description || 'Пользователь не добавил информацию о себе' }}
              </div>
            </div>
          </div>

          <div class="profile-actions">
            <button 
              @click="editProfile" 
              class="action-button edit-button"
            >
              Редактировать профиль
            </button>
            <button 
              v-if="userRole === 'executor'"
              @click="$router.push('/myReviews')" 
              class="action-button reviews-button"
            >
              Мои отзывы
            </button>
          </div>
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
  name: 'MyProfilePage',
  data() {
    return {
      userData: {
        login: '',
        date: '',
        name: '',
        oranization: '',
        description: '',
        level: null,
        loyality: null
      },
      userRole: '',
      userId: null,
      loading: true,
      error: null
    }
  },
  async created() {
    await this.verifyToken();
    await this.fetchUserData();
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
        this.userId = decoded.user_id;
        this.userRole = decoded.role;
      } catch (error) {
        localStorage.removeItem('accessToken');
        this.$router.push('/login');
      }
    },
    
    async fetchUserData() {
      this.loading = true;
      try {
        const token = localStorage.getItem('accessToken');
        const endpoint = this.userRole === 'employer' 
          ? `${config.endpoints.admin}getEmployer/` 
          : `${config.endpoints.admin}getExecutor/`;
        
        const response = await axios.get(endpoint, {
          params: { id: this.userId },
          headers: { 'Authorization': token }
        });
        
        if (response.data && response.data.length > 0) {
          const data = response.data[0];
          this.userData = {
            login: data.login || '',
            date: data.date || '',
            name: data.name || '',
            oranization: data.oranization || '',
            description: data.description || '',
            level: data.level !== undefined ? data.level : null,
            loyality: data.loyality !== undefined ? data.loyality : null
          };
        }
      } catch (error) {
        console.error('Ошибка загрузки данных профиля:', error);
        this.error = 'Не удалось загрузить данные профиля';
      } finally {
        this.loading = false;
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      });
    },
    
    editProfile() {
      this.$router.push('/editProfile');
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
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 30px;
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

.user-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-info {
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

.main-content {
  flex: 1;
  padding: 30px;
  background-color: #f5f7fa;
}

.profile-container {
  max-width: 800px;
  margin: 0 auto;
}

.profile-header {
  margin-bottom: 30px;
  text-align: center;
}

.profile-title {
  color: #2c3e50;
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 5px;
}

.profile-date {
  color: #666;
  font-size: 14px;
}

.profile-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 30px;
}

.profile-info {
  margin-bottom: 30px;
}

.info-section {
  margin-bottom: 25px;
}

.section-title {
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.info-row {
  display: flex;
  margin-bottom: 12px;
}

.info-label {
  font-weight: 500;
  color: #555;
  width: 150px;
}

.info-value {
  color: #333;
  flex: 1;
}

.description {
  color: #444;
  line-height: 1.6;
}

.profile-actions {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.action-button {
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
}

.edit-button {
  background-color: #2196F3;
  color: white;
}

.edit-button:hover {
  background-color: #0b7dda;
}

.reviews-button {
  background-color: #FF9800;
  color: white;
}

.reviews-button:hover {
  background-color: #e68a00;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    padding: 15px;
    height: auto;
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
  
  .main-content {
    padding: 15px;
  }
  
  .info-row {
    flex-direction: column;
    gap: 5px;
  }
  
  .info-label {
    width: 100%;
  }
  
  .profile-actions {
    flex-direction: column;
    gap: 10px;
  }
  
  .action-button {
    width: 100%;
  }
}
</style>