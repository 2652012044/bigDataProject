<template>
  <el-menu
    :default-active="activeMenu"
    :collapse="collapsed"
    class="side-menu"
    router
  >
    <template v-for="item in menuItems" :key="item.path">
      <el-menu-item :index="item.path">
        <el-icon><component :is="item.icon" /></el-icon>
        <template #title>{{ item.title }}</template>
      </el-menu-item>
    </template>
  </el-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const appStore = useAppStore()
const collapsed = computed(() => appStore.sideMenuCollapsed)
const activeMenu = computed(() => route.path)

const menuConfig = {
  book: [
    { path: '/book/keyword', title: '关键词分析', icon: 'Search' },
    { path: '/book/topic', title: '主题分析', icon: 'ChatDotSquare' },
    { path: '/book/type', title: '类型统计', icon: 'PieChart' }
  ],
  sentiment: [
    { path: '/sentiment/classify', title: '情感分类', icon: 'ChatLineSquare' },
    { path: '/sentiment/reputation', title: '口碑评分', icon: 'Star' },
    { path: '/sentiment/hotspot', title: '热点分析', icon: 'Sunny' },
    { path: '/sentiment/predict', title: '情感预测', icon: 'MagicStick' }
  ],
  recommend: [
    { path: '/recommend/hot', title: '热门推荐', icon: 'Pointer' },
    { path: '/recommend/category', title: '同类别推荐', icon: 'Grid' },
    { path: '/recommend/similar', title: '相似推荐', icon: 'Connection' }
  ],
  trend: [
    { path: '/trend/type', title: '类型趋势', icon: 'TrendCharts' },
    { path: '/trend/heat', title: '热度趋势', icon: 'DataLine' },
    { path: '/trend/keyword', title: '关键词趋势', icon: 'Promotion' }
  ],
  data: [
    { path: '/data/cleaning', title: '清洗日志', icon: 'Document' }
  ],
  export: [
    { path: '/export', title: '生成报告', icon: 'Download' }
  ]
}

const menuItems = computed(() => {
  const module = route.meta.module
  return menuConfig[module] || []
})
</script>

<style lang="scss" scoped>
.side-menu {
  height: 100%;
  border-right: none;

  &:not(.el-menu--collapse) {
    width: 200px;
  }
}
</style>
