import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/pages/HomePage.vue')
  },
  {
    path: '/session/:sessionId',
    name: 'SessionDetail',
    component: () => import('@/pages/SessionDetail.vue')
  },
  {
    path: '/report/:reportId',
    name: 'ReportDetail',
    component: () => import('@/pages/ReportDetail.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
