import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginForm.vue'),
    },
    {
      path: '/tasks',
      name: 'Tasks',
      component: () => import('../views/TasksForm.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('../views/RegistrationForm.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/task/:id',
      name: 'TaskDetail',
      component:  () => import('../views/LookTaskForm.vue'),
      meta: {
        requiresAuth: true
      }
    },
    {
      path: '/task/:id/responses',
      name: 'Votes',
      component: () => import('../views/VotesForm.vue'),
      meta: { requiresAuth: true, role: 'employer' }
    },
    {
      path: '/userInfo/:id',
      name: 'UserInfo',
      component:  () => import('../views/UserInfoForm.vue'),
      meta: {
        requiresAuth: true
      }
    },
    {
      path: '/myTasks',
      name: 'MyTasks',
      component: () => import('../views/MyTasksForm.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/createTask',
      name: 'CreateTask',
      component: () => import('../views/CreateTaskForm.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/myPayments',
      name: 'MyPayments',
      component: () => import('../views/MyPaymentsForm.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/deposit',
      name: 'Deposit',
      component: () => import('../views/DepositForm.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/withdraw',
      name: 'Withdraw',
      component: () => import('../views/WithdrawForm.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/myProfile',
      name: 'MyProfile',
      component: () => import('../views/MyProfileForm.vue'),
      meta: { requiresAuth: true }
    },
  ],
})

export default router
