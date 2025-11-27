import { createRouter, createWebHistory } from 'vue-router'
import ContextView from '@/components/ContextView.vue'
import PatchesView from '@/components/PatchesView.vue'
import SessionsView from '@/components/SessionsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'context',
      component: ContextView,
      meta: { title: 'Context Restoration' }
    },
    {
      path: '/patches',
      name: 'patches',
      component: PatchesView,
      meta: { title: 'Patches' }
    },
    {
      path: '/sessions',
      name: 'sessions',
      component: SessionsView,
      meta: { title: 'Coding Sessions' }
    }
  ]
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'DevMemory'} | DevMemory Dashboard`
  next()
})

export default router
