<template>
  <el-container class="app-layout">
    <el-header class="app-header" height="56px">
      <TopNav />
    </el-header>
    <el-container class="app-body">
      <el-aside :width="sideMenuCollapsed ? '64px' : '200px'" class="app-aside" v-if="showSideMenu">
        <SideMenu />
      </el-aside>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import TopNav from './TopNav.vue'
import SideMenu from './SideMenu.vue'

const route = useRoute()
const appStore = useAppStore()
const sideMenuCollapsed = computed(() => appStore.sideMenuCollapsed)

// 首页和搜索页不显示侧边栏
const showSideMenu = computed(() => {
  const module = route.meta.module
  return module && !['home', 'search', 'favorites', 'export'].includes(module)
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.app-layout {
  height: 100vh;
  overflow: hidden;
}

.app-header {
  padding: 0;
  border-bottom: 1px solid $border-light;
  box-shadow: $box-shadow-light;
  z-index: 100;
}

.app-body {
  height: calc(100vh - $top-nav-height);
  overflow: hidden;
}

.app-aside {
  border-right: 1px solid $border-light;
  background: $bg-white;
  transition: width 0.3s;
  overflow: hidden;
}

.app-main {
  background: $bg-page;
  padding: 0;
  overflow-y: auto;
}
</style>
