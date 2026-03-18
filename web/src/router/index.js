import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { title: '登录', noAuth: true, noLayout: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/register/RegisterView.vue'),
    meta: { title: '注册', noAuth: true, noLayout: true }
  },
  {
    path: '/bigscreen',
    name: 'BigScreen',
    component: () => import('@/views/bigscreen/BigScreen.vue'),
    meta: { title: '数据可视化大屏', noLayout: true }
  },
  {
    path: '/',
    component: () => import('@/layout/AppLayout.vue'),
    redirect: '/home',
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/home/HomeView.vue'),
        meta: { title: '首页', module: 'home' }
      },
      // 书籍特征分析
      {
        path: 'book/keyword',
        name: 'KeywordAnalysis',
        component: () => import('@/views/bookAnalysis/KeywordAnalysis.vue'),
        meta: { title: '关键词分析', module: 'book' }
      },
      {
        path: 'book/topic',
        name: 'TopicAnalysis',
        component: () => import('@/views/bookAnalysis/TopicAnalysis.vue'),
        meta: { title: '主题分析', module: 'book' }
      },
      {
        path: 'book/type',
        name: 'TypeStatistics',
        component: () => import('@/views/bookAnalysis/TypeStatistics.vue'),
        meta: { title: '类型统计', module: 'book' }
      },
      // 情感分析
      {
        path: 'sentiment/classify',
        name: 'SentimentClassify',
        component: () => import('@/views/sentiment/SentimentClassify.vue'),
        meta: { title: '情感分类', module: 'sentiment' }
      },
      {
        path: 'sentiment/reputation',
        name: 'ReputationScore',
        component: () => import('@/views/sentiment/ReputationScore.vue'),
        meta: { title: '口碑评分', module: 'sentiment' }
      },
      {
        path: 'sentiment/hotspot',
        name: 'HotspotAnalysis',
        component: () => import('@/views/sentiment/HotspotAnalysis.vue'),
        meta: { title: '热点分析', module: 'sentiment' }
      },
      // 推荐模块
      {
        path: 'recommend/hot',
        name: 'HotRecommend',
        component: () => import('@/views/recommend/HotRecommend.vue'),
        meta: { title: '热门推荐', module: 'recommend' }
      },
      {
        path: 'recommend/category',
        name: 'CategoryRecommend',
        component: () => import('@/views/recommend/CategoryRecommend.vue'),
        meta: { title: '同类别推荐', module: 'recommend' }
      },
      {
        path: 'recommend/similar',
        name: 'SimilarRecommend',
        component: () => import('@/views/recommend/SimilarRecommend.vue'),
        meta: { title: '相似推荐', module: 'recommend' }
      },
      // 我的收藏
      {
        path: 'favorites',
        name: 'Favorites',
        component: () => import('@/views/favorites/FavoritesView.vue'),
        meta: { title: '我的收藏', module: 'favorites' }
      },
      // 市场趋势
      {
        path: 'trend/type',
        name: 'TypeTrend',
        component: () => import('@/views/trend/TypeTrend.vue'),
        meta: { title: '类型趋势', module: 'trend' }
      },
      {
        path: 'trend/heat',
        name: 'HeatTrend',
        component: () => import('@/views/trend/HeatTrend.vue'),
        meta: { title: '热度趋势', module: 'trend' }
      },
      {
        path: 'trend/keyword',
        name: 'KeywordTrend',
        component: () => import('@/views/trend/KeywordTrend.vue'),
        meta: { title: '关键词趋势', module: 'trend' }
      },
      // 搜索结果
      {
        path: 'search',
        name: 'SearchResult',
        component: () => import('@/views/search/SearchResult.vue'),
        meta: { title: '搜索结果', module: 'search' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 小说大数据平台` : '小说大数据平台'

  if (to.meta.noAuth) {
    next()
    return
  }

  const userStore = useUserStore()
  if (!userStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
