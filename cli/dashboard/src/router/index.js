import { createRouter, createWebHistory } from 'vue-router'
import SessionsView from '@/components/SessionsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'sessions',
      component: SessionsView,
      meta: { title: 'Sessions' }
    }
  ]
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'DevMemory'} | DevMemory`
  next()
})

export default router
