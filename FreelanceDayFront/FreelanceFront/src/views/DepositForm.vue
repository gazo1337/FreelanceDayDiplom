<template>
  <div class="deposit-container">
    <div class="deposit-header">
      <h1>Пополнение баланса</h1>
      <button class="close-button" @click="goBack">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <div class="deposit-content">
      <div class="payment-card">
        <div class="card-header">
          <div class="card-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
              <line x1="1" y1="10" x2="23" y2="10"></line>
            </svg>
          </div>
          <h2>Введите данные для пополнения</h2>
        </div>

        <div class="form-group">
          <label for="amount">Сумма пополнения (₽)</label>
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
        </div>

        <div class="form-group">
          <label>Способ оплаты</label>
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

        <div class="form-group">
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

        <div class="card-details">
          <div class="form-group">
            <label for="expiry">Срок действия</label>
            <input 
              id="expiry"
              v-model="expiry"
              type="text"
              placeholder="MM/ГГ"
              maxlength="5"
              class="form-input"
              @input="formatExpiry"
            >
          </div>
          <div class="form-group">
            <label for="cvv">CVV/CVC</label>
            <input 
              id="cvv"
              v-model="cvv"
              type="password"
              placeholder="•••"
              maxlength="3"
              class="form-input"
            >
          </div>
        </div>

        <button 
          class="submit-button"
          :disabled="!isFormValid || processing"
          @click="processPayment"
        >
          <span v-if="!processing">Пополнить на {{ amount }} ₽</span>
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
          <span>Безопасная оплата через SSL</span>
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
          <h3>Платёж успешно завершён!</h3>
          <p>Ваш счёт пополнен на {{ amount }} ₽</p>
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

export default {
  name: 'DepositPage',
  data() {
    return {
      amount: 1000,
      cardNumber: '',
      expiry: '',
      cvv: '',
      selectedMethod: 'bankcard',
      processing: false,
      showSuccess: false,
      userLogin: '',
      userId: null,
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
      return (
        this.amount >= 100 &&
        this.cardNumber.replace(/\s/g, '').length === 16 &&
        this.expiry.length === 5 &&
        this.cvv.length === 3
      );
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
        this.userId = decoded.user_id;
      } catch (error) {
        localStorage.removeItem('accessToken');
        this.$router.push('/login');
      }
    },
    
    setAmount(amount) {
      this.amount = amount;
    },
    
    validateAmount() {
      if (this.amount < 100) {
        this.amount = 100;
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
    
    formatExpiry() {
      let exp = this.expiry.replace(/\D/g, '');
      
      if (exp.length > 2) {
        exp = exp.substring(0, 2) + '/' + exp.substring(2);
      }
      
      if (exp.length > 5) {
        exp = exp.substring(0, 5);
      }
      
      this.expiry = exp;
    },
    
    async processPayment() {
      if (!this.isFormValid || this.processing) return;
      
      this.processing = true;
      
      try {
        const token = localStorage.getItem('accessToken');
        const currentDate = new Date().toISOString().split('T')[0];
        
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        await axios.post(
          'http://127.0.0.1:8000/adminPayment/payment/toEmployer/',
          null,
          {
            params: {
              id: this.userId,
              count: this.amount,
              date: currentDate
            },
            headers: { 
              'Authorization': token 
            }
          }
        );
        
        this.showSuccess = true;
      } catch (error) {
        console.error('Ошибка платежа:', error);
        alert('Произошла ошибка при обработке платежа. Пожалуйста, попробуйте позже.');
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
.deposit-container {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Roboto', sans-serif;
  color: #333;
  min-height: 100vh;
  background-color: #f8f9fa;
}

.deposit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  position: relative;
}

.deposit-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #2c3e50;
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

.card-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
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
  .deposit-container {
    padding: 15px;
  }
  
  .card-details {
    grid-template-columns: 1fr;
  }
  
  .quick-amounts {
    flex-wrap: wrap;
  }
  
  .quick-amounts button {
    min-width: calc(50% - 5px);
  }
}
</style>