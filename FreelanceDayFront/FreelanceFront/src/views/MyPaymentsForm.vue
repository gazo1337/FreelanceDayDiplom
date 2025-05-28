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
            v-if="userRole === 'employer'"
            @click="$router.push('/createTask')" 
            class="nav-button"
          >
            Создать задачу
          </button>
          <button 
            v-if="userRole === 'executor'"
            @click="$router.push('/tasks')" 
            class="nav-button"
            :class="{ 'active': $route.path === '/tasks' }"
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
      <div class="payments-container">
        <h2 class="page-title">Мои финансы</h2>
        
        <div class="balance-card">
          <div class="balance-info">
            <span class="balance-label">Текущий баланс:</span>
            <span class="balance-amount">{{ balance }} ₽</span>
          </div>
          
          <button 
            v-if="userRole === 'executor'"
            @click="$router.push('/withdraw')" 
            class="action-button withdraw-button"
          >
            Вывести средства
          </button>
          
          <button 
            v-else-if="userRole === 'employer'"
            @click="$router.push('/deposit')" 
            class="action-button deposit-button"
          >
            Пополнить счёт
          </button>
        </div>
        
        <div class="transactions-section">
          <h3 class="section-title">История операций</h3>
          <div v-if="loading" class="loading">Загрузка операций...</div>
          <div v-else-if="error" class="error-message">{{ error }}</div>
          <div v-else-if="transactions.length === 0" class="no-transactions">
            Нет операций
          </div>
          <div v-else class="transactions-list">
            <div 
              v-for="transaction in transactions" 
              :key="transaction.payment_id"
              class="transaction-item"
              :class="getTransactionClass(transaction)"
            >
              <div class="transaction-info">
                <span class="transaction-amount">
                  {{ Math.abs(transaction.payment_count) }} ₽
                  <span class="transaction-type">
                    {{ getTransactionType(transaction) }}
                  </span>
                </span>
                <span class="transaction-date">
                  {{ formatDate(transaction.payment_dttm) }}
                </span>
              </div>
              <div class="transaction-description">
                {{ getTransactionDescription(transaction) }}
              </div>
            </div>
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
  name: 'MyPaymentsPage',
  data() {
    return {
      balance: 0,
      transactions: [],
      loading: false,
      error: null,
      userLogin: '',
      userRole: '',
      userId: null
    }
  },
  async created() {
    await this.verifyToken();
    await this.fetchBalance();
    await this.fetchTransactions();
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
      this.loading = true;
      try {
        const token = localStorage.getItem('accessToken');
        const response = await axios.get(
          `http://127.0.0.1:8000/adminPayment/getBalance/?id=${this.userId}&role=${this.userRole}`,
          { headers: { 'Authorization': token } }
        );
        this.balance = parseFloat(response.data.balance);
      } catch (error) {
        console.error('Ошибка загрузки баланса:', error);
        this.error = 'Не удалось загрузить информацию о балансе';
      } finally {
        this.loading = false;
      }
    },
    
    async fetchTransactions() {
      this.loading = true;
      try {
        const token = localStorage.getItem('accessToken');
        const response = await axios.get(
          'http://127.0.0.1:8000/adminPayment/payment/getOperations/',
          {
            params: {
              id: this.userId,
              role: this.userRole
            },
            headers: { 
              'Authorization': token 
            }
          }
        );
        
        if (response.data.status === 'success') {
          this.transactions = response.data.results || [];
        } else {
          this.transactions = [];
        }
      } catch (error) {
        console.error('Ошибка загрузки операций:', error);
        this.error = 'Не удалось загрузить историю операций';
        this.transactions = [];
      } finally {
        this.loading = false;
      }
    },
    
    getTransactionClass(transaction) {
      return transaction.reciever_id == this.userId ? 'income' : 'outcome';
    },
    
    getTransactionType(transaction) {
      return transaction.reciever_id == this.userId ? '(зачисление)' : '(списание)';
    },
    
    getTransactionDescription(transaction) {
      if (transaction.reciever_id == this.userId) {
        return this.userRole === 'employer' 
          ? 'Возврат средств' 
          : `Оплата за задачу #${transaction.task_id}`;
      } else {
        return this.userRole === 'employer'
          ? `Оплата задачи #${transaction.task_id}`
          : 'Вывод средств';
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

.payments-container {
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 30px;
  font-size: 24px;
  font-weight: 600;
}

.balance-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 25px;
  margin-bottom: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.balance-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.balance-label {
  font-size: 16px;
  color: #555;
}

.balance-amount {
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
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

.withdraw-button {
  background-color: #2196F3;
  color: white;
}

.withdraw-button:hover {
  background-color: #0b7dda;
}

.deposit-button {
  background-color: #4CAF50;
  color: white;
}

.deposit-button:hover {
  background-color: #45a049;
}

.transactions-section {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 25px;
}

.section-title {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 20px;
  font-weight: 600;
}

.transactions-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.transaction-item {
  padding: 15px;
  border-radius: 6px;
  border-left: 4px solid transparent;
  transition: all 0.3s;
}

.transaction-item.income {
  border-left-color: #4CAF50;
  background-color: #e8f5e9;
}

.transaction-item.outcome {
  border-left-color: #f44336;
  background-color: #ffebee;
}

.transaction-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.transaction-amount {
  font-weight: 600;
  color: #666;
}

.transaction-type {
  font-size: 0.8em;
  color: #666;
  margin-left: 5px;
}

.transaction-date {
  color: #666;
  font-size: 14px;
}

.transaction-description {
  color: #444;
}

.loading, .no-transactions {
  text-align: center;
  padding: 20px;
  color: #666;
}

.error-message {
  padding: 15px;
  background-color: #ffebee;
  color: #d32f2f;
  border-radius: 6px;
  text-align: center;
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
  
  .balance-card {
    flex-direction: column;
    gap: 20px;
    align-items: flex-start;
  }
  
  .main-content {
    padding: 15px;
  }
}
</style>