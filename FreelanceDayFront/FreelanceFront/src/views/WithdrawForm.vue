<template>
  <div class="withdraw-container">
    <div class="withdraw-header">
      <h1>Вывод средств</h1>
      <button class="close-button" @click="goBack">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <div class="withdraw-content">
      <div class="payment-card">
        <div class="card-header">
          <div class="card-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
              <line x1="1" y1="10" x2="23" y2="10"></line>
            </svg>
          </div>
          <h2>Введите данные для вывода</h2>
        </div>

        <div class="form-group">
          <label for="amount">Сумма вывода (₽)</label>
          <input 
            id="amount"
            v-model="amount"
            type="number"
            min="100"
            step="100"
            placeholder="1000"
            class="form-input"
            @input="validateAmount"
          >
          <div class="quick-amounts">
            <button 
              v-for="sum in quickAmounts" 
              :key="sum"
              @click="setAmount(sum)"
              :class="{ 'active': amount == sum }"
            >
              {{ sum }} ₽
            </button>
          </div>
          <div class="balance-info">
            Доступно для вывода: {{ availableBalance }} ₽
          </div>
        </div>

        <div class="form-group">
          <label>Способ вывода</label>
          <div class="payment-methods">
            <div 
              v-for="method in paymentMethods"
              :key="method.id"
              class="payment-method"
              :class="{ 'selected': selectedMethod === method.id }"
              @click="selectedMethod = method.id"
            >
              <img :src="method.icon" :alt="method.name" class="method-icon">
              <span>{{ method.name }}</span>
              <div class="checkmark" v-if="selectedMethod === method.id">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4CAF50" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div class="form-group" v-if="selectedMethod === 'bankcard'">
          <label for="card-number">Номер карты</label>
          <div class="card-input">
            <input 
              id="card-number"
              v-model="cardNumber"
              type="text"
              placeholder="1234 5678 9012 3456"
              maxlength="19"
              class="form-input"
              @input="formatCardNumber"
            >
            <div class="card-type">
              <img v-if="cardType" :src="cardType.icon" :alt="cardType.name">
            </div>
          </div>
        </div>

        <div class="form-group" v-if="selectedMethod === 'qiwi' || selectedMethod === 'yoomoney'">
          <label for="wallet-number">{{ selectedMethod === 'qiwi' ? 'QIWI Кошелёк' : 'ЮMoney Кошелёк' }}</label>
          <input 
            id="wallet-number"
            v-model="walletNumber"
            type="text"
            :placeholder="selectedMethod === 'qiwi' ? '+7XXXXXXXXXX' : 'Номер кошелька'"
            class="form-input"
          >
        </div>

        <button 
          class="submit-button"
          :disabled="!isFormValid || processing"
          @click="processWithdrawal"
        >
          <span v-if="!processing">Вывести {{ amount }} ₽</span>
          <span v-else class="processing">
            <svg class="spinner" viewBox="0 0 50 50">
              <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5"></circle>
            </svg>
            Обработка...
          </span>
        </button>

        <div class="secure-payment">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4CAF50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
          <span>Безопасный перевод через SSL</span>
        </div>
      </div>
    </div>

    <transition name="fade">
      <div v-if="showSuccess" class="success-modal">
        <div class="success-content">
          <div class="success-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#4CAF50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <h3>Вывод средств успешно завершён!</h3>
          <p>Средства будут зачислены в течение 1-3 рабочих дней</p>
          <button class="success-button" @click="redirectToPayments">
            Вернуться в финансы
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import config from '../config/api.js';

export default {
  name: 'WithdrawPage',
  data() {
    return {
      amount: 1000,
      availableBalance: 0,
      cardNumber: '',
      walletNumber: '',
      selectedMethod: 'bankcard',
      processing: false,
      showSuccess: false,
      userId: null,
      taskId: null,
      paymentMethods: [
        {
          id: 'bankcard',
          name: 'Банковская карта',
          icon: 'https://cdn-icons-png.flaticon.com/512/196/196578.png'
        },
        {
          id: 'qiwi',
          name: 'QIWI Кошелёк',
          icon: 'https://cdn-icons-png.flaticon.com/512/196/196561.png'
        },
        {
          id: 'yoomoney',
          name: 'ЮMoney',
          icon: 'https://cdn-icons-png.flaticon.com/512/196/196565.png'
        }
      ],
      quickAmounts: [500, 1000, 2000, 5000],
      cardTypes: {
        visa: {
          name: 'Visa',
          icon: 'https://cdn-icons-png.flaticon.com/512/196/196578.png',
          pattern: /^4/
        },
        mastercard: {
          name: 'Mastercard',
          icon: 'https://cdn-icons-png.flaticon.com/512/196/196561.png',
          pattern: /^5[1-5]/
        },
        mir: {
          name: 'Мир',
          icon: 'https://cdn-icons-png.flaticon.com/512/196/196565.png',
          pattern: /^2/
        }
      }
    }
  },
  computed: {
    isFormValid() {
      const basicValidation = this.amount >= 100 && this.amount <= this.availableBalance;
      
      if (this.selectedMethod === 'bankcard') {
        return basicValidation && this.cardNumber.replace(/\s/g, '').length === 16;
      } else if (this.selectedMethod === 'qiwi') {
        return basicValidation && this.walletNumber.length >= 11;
      } else if (this.selectedMethod === 'yoomoney') {
        return basicValidation && this.walletNumber.length > 0;
      }
      
      return false;
    },
    cardType() {
      const num = this.cardNumber.replace(/\s/g, '');
      for (const type in this.cardTypes) {
        if (this.cardTypes[type].pattern.test(num)) {
          return this.cardTypes[type];
        }
      }
      return null;
    }
  },
  async created() {
    await this.verifyToken();
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
        this.userId = decoded.user_id;
        this.taskId = this.$route.params.taskId;
      } catch (error) {
        localStorage.removeItem('accessToken');
        this.$router.push('/login');
      }
    },
    
    async fetchBalance() {
      try {
        const token = localStorage.getItem('accessToken');
        const response = await axios.get(
          `${config.endpoints.payments}getBalance/`,
          {
            params: {
              id: this.userId,
              role: 'executor'
            },
            headers: { 
              'Authorization': token 
            }
          }
        );
        this.availableBalance = response.data.balance;
      } catch (error) {
        console.error('Ошибка при получении баланса:', error);
        alert('Не удалось получить информацию о балансе');
      }
    },
    
    setAmount(amount) {
      this.amount = amount;
    },
    
    validateAmount() {
      if (this.amount < 100) {
        this.amount = 100;
      } else if (this.amount > this.availableBalance) {
        this.amount = this.availableBalance;
      }
    },
    
    formatCardNumber() {
      let num = this.cardNumber.replace(/\D/g, '');
      num = num.replace(/(\d{4})(?=\d)/g, '$1 ');
      if (num.length > 19) {
        num = num.substring(0, 19);
      }
      this.cardNumber = num;
    },
    
    async processWithdrawal() {
      if (!this.isFormValid || this.processing) return;
      
      this.processing = true;
      
      try {
        const token = localStorage.getItem('accessToken');
        const currentDate = new Date().toISOString().split('T')[0];
        await new Promise(resolve => setTimeout(resolve, 3000));
        await axios.post(
          `${config.endpoints.payments}payment/fromExecutor/`,
          null,
          {
            params: {
              ExecutorID: this.userId,
              count: this.amount,
              date: currentDate
            },
            headers: { 
              'Authorization': token 
            }
          }
        );
        
        this.showSuccess = true;
        await this.fetchBalance();
      } catch (error) {
        console.error('Ошибка вывода:', error);
        alert('Произошла ошибка при обработке вывода. Пожалуйста, попробуйте позже.');
      } finally {
        this.processing = false;
      }
    },
    
    goBack() {
      this.$router.go(-1);
    },
    
    redirectToPayments() {
      this.$router.push('/myPayments');
    }
  }
}
</script>

<style scoped>
.withdraw-container {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Roboto', sans-serif;
  color: #333;
  min-height: 100vh;
  background-color: #f8f9fa;
}

.withdraw-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  position: relative;
}

.withdraw-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #2c3e50;
}

.balance-info {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

.close-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  color: #666;
  transition: color 0.3s;
}

.close-button:hover {
  color: #333;
}

.payment-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 25px;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 25px;
}

.card-icon {
  width: 40px;
  height: 40px;
  background-color: #f0f4ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}

.card-header h2 {
  font-size: 18px;
  font-weight: 500;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #555;
}

.form-input {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.form-input:focus {
  border-color: #4CAF50;
  outline: none;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.quick-amounts {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.quick-amounts button {
  flex: 1;
  padding: 8px;
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.quick-amounts button:hover {
  background-color: #e0e0e0;
}

.quick-amounts button.active {
  background-color: #4CAF50;
  color: white;
  border-color: #4CAF50;
}

.payment-methods {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.payment-method {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.payment-method:hover {
  border-color: #bbb;
}

.payment-method.selected {
  border-color: #4CAF50;
  background-color: #f0f8f0;
}

.method-icon {
  width: 24px;
  height: 24px;
  margin-right: 10px;
}

.checkmark {
  margin-left: auto;
}

.card-input {
  position: relative;
}

.card-type {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
}

.card-type img {
  height: 24px;
}

.submit-button {
  width: 100%;
  padding: 15px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-top: 20px;
}

.submit-button:hover:not(:disabled) {
  background-color: #45a049;
}

.submit-button:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

.processing {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.spinner {
  animation: rotate 2s linear infinite;
  width: 20px;
  height: 20px;
}

.spinner .path {
  stroke: white;
  stroke-linecap: round;
  animation: dash 1.5s ease-in-out infinite;
}

@keyframes rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

.secure-payment {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

.success-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.success-content {
  background: white;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  max-width: 400px;
  width: 90%;
}

.success-icon {
  margin-bottom: 20px;
}

.success-content h3 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #2c3e50;
}

.success-content p {
  color: #555;
  margin-bottom: 20px;
}

.success-button {
  padding: 12px 24px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.success-button:hover {
  background-color: #45a049;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}

@media (max-width: 480px) {
  .withdraw-container {
    padding: 15px;
  }
  
  .quick-amounts {
    flex-wrap: wrap;
  }
  
  .quick-amounts button {
    min-width: calc(50% - 5px);
  }
}
</style>