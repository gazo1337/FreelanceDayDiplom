<template>
  <div class="app-container">
    <header class="header">
      <div class="header-left">
        <h1 class="site-title">FreeLanceDay!</h1>
        <nav class="header-nav">
          <button 
            @click="$router.push('/myProfile')" 
            class="nav-button"
          >
            Мой профиль
          </button>
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
            v-if="currentUserRole === 'executor'"
            @click="$router.push('/tasks')" 
            class="nav-button"
          >
            Поиск задач
          </button>
          <button 
            v-if="currentUserRole === 'employer'"
            @click="$router.push('/createTask')" 
            class="nav-button"
          >
            Создать задачу
          </button>
        </nav>
      </div>
      <div class="user-controls">
        <div class="user-info">
          {{ currentUserLogin }}
        </div>
        <button @click="logout" class="logout-button">Выйти</button>
      </div>
    </header>

    <main class="main-content">
      <div class="profile-container">
        <div class="profile-header">
          <h2 class="profile-title">Профиль пользователя</h2>
          <span class="profile-date">На платформе с {{ formatDate(userData.date) }}</span>
        </div>

        <div class="profile-card">
          <div class="profile-info">
            <div class="info-section">
              <h3 class="section-title">Основная информация</h3>
              <div class="info-row">
                <span class="info-label">Логин:</span>
                <span class="info-value">{{ userData.login }}</span>
              </div>
              
              <div class="info-row">
                <span class="info-label">Роль:</span>
                <span class="info-value">{{ mapRole(userData.role) }}</span>
              </div>
              
              <div v-if="userData.role === 'employer'" class="info-row">
                <span class="info-label">Организация:</span>
                <span class="info-value">{{ userData.oranization || 'Не указано' }}</span>
              </div>
              
              <div v-if="userData.role === 'executor'" class="info-row">
                <span class="info-label">Уровень:</span>
                <span class="info-value">{{ userData.level !== null && userData.level !== undefined ? userData.level : 'Не указан' }}</span>
              </div>
              
              <div v-if="userData.role === 'executor'" class="info-row">
                <span class="info-label">Рейтинг лояльности:</span>
                <span class="info-value">{{ userData.loyality !== null && userData.loyality !== undefined ? userData.loyality : 'Не указан' }}</span>
              </div>
            </div>

            <div class="info-section">
              <h3 class="section-title">О пользователе</h3>
              <div class="description">
                {{ userData.description || 'Пользователь не добавил информацию о себе' }}
              </div>
            </div>
          </div>

          <div v-if="userData.role === 'executor'" class="profile-actions">
            <button 
              @click="$router.push(`/userReviews/${userId}`)" 
              class="action-button reviews-button"
            >
              Отзывы о пользователе
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

export default {
  name: 'UserInfoPage',
  data() {
    return {
      userId: null,
      userData: {
        login: '',
        role: '',
        date: '',
        name: '',
        oranization: '',
        description: '',
        level: null,
        loyality: null
      },
      currentUserLogin: '',
      currentUserRole: '',
      currentUserId: null,
      loading: true,
      error: null
    }
  },
  async created() {
    this.userId = this.$route.params.id;
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
        this.currentUserId = decoded.user_id;
        this.currentUserRole = decoded.role;
        this.currentUserLogin = decoded.login;
      } catch (error) {
        localStorage.removeItem('accessToken');
        this.$router.push('/login');
      }
    },
    
    async fetchUserData() {
      this.loading = true;
      try {
        const token = localStorage.getItem('accessToken');
        const userResponse = await axios.get(
          'http://127.0.0.1:8000/administration/getUserById/',
          {
            params: { id: this.userId },
            headers: { 'Authorization': token }
          }
        );
        
        if (userResponse.data && userResponse.data.length > 0) {
          const userBasicInfo = userResponse.data[0];
          this.userData.login = userBasicInfo.login;
          this.userData.role = userBasicInfo.role;
          this.userData.date = userBasicInfo.date;
          const endpoint = userBasicInfo.role === 'employer' 
            ? 'http://127.0.0.1:8000/administration/getEmployer/' 
            : 'http://127.0.0.1:8000/administration/getExecutor/';
          
          const detailResponse = await axios.get(endpoint, {
            params: { id: this.userId },
            headers: { 'Authorization': token }
          });
          
          if (detailResponse.data && detailResponse.data.length > 0) {
            const detailData = detailResponse.data[0];
            this.userData.name = detailData.name || '';
            this.userData.oranization = detailData.oranization || '';
            this.userData.description = detailData.description || '';
            if (userBasicInfo.role === 'executor') {
              this.userData.level = detailData.level !== undefined ? detailData.level : null;
              this.userData.loyality = detailData.loyality !== undefined ? detailData.loyality : null;
            }
          }
        }
      } catch (error) {
        console.error('Ошибка загрузки данных пользователя:', error);
        this.error = 'Не удалось загрузить данные пользователя';
      } finally {
        this.loading = false;
      }
    },
    
    mapRole(role) {
      return role === 'employer' ? 'Заказчик' : 'Исполнитель';
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