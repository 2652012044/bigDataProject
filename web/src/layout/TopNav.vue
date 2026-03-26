<template>
  <div class="top-nav">
    <div class="nav-left">
      <div class="logo" @click="$router.push('/home')">
        <el-icon :size="24"><DataAnalysis /></el-icon>
        <span class="logo-text">小说大数据平台</span>
      </div>
      <el-menu
        :default-active="activeModule"
        mode="horizontal"
        class="nav-menu"
        @select="handleModuleSelect"
        :ellipsis="false"
      >
        <el-menu-item index="home">首页</el-menu-item>
        <el-menu-item index="book">书籍分析</el-menu-item>
        <el-menu-item index="sentiment">情感分析</el-menu-item>
        <el-menu-item index="recommend">智能推荐</el-menu-item>
        <el-menu-item index="trend">市场趋势</el-menu-item>
        <el-menu-item index="data">数据管理</el-menu-item>
        <el-menu-item index="export">报告导出</el-menu-item>
        <el-menu-item index="bigscreen">数据大屏</el-menu-item>
      </el-menu>
    </div>

    <div class="nav-right">
      <el-input
        v-model="searchText"
        placeholder="搜索小说..."
        class="search-input"
        @keyup.enter="handleSearch"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-dropdown trigger="click" @command="handleCommand">
        <div class="user-avatar">
          <el-avatar :size="32" :icon="UserFilled" />
          <span class="username">{{ username }}</span>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="favorites">
              <el-icon><Star /></el-icon>我的收藏
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided>
              <el-icon><SwitchButton /></el-icon>退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { UserFilled } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()

const searchText = ref('')
const username = computed(() => userStore.username || '用户')
const activeModule = computed(() => route.meta.module || 'home')

const moduleDefaultRoute = {
  home: '/home',
  book: '/book/keyword',
  sentiment: '/sentiment/classify',
  recommend: '/recommend/hot',
  trend: '/trend/heat',
  data: '/data/cleaning',
  export: '/export',
  bigscreen: '/bigscreen'
}

function handleModuleSelect(index) {
  const target = moduleDefaultRoute[index]
  if (target) {
    if (index === 'bigscreen') {
      window.open(router.resolve(target).href, '_blank')
    } else {
      router.push(target)
    }
  }
}

function handleSearch() {
  if (searchText.value.trim()) {
    appStore.setSearchKeyword(searchText.value.trim())
    router.push({ name: 'SearchResult', query: { q: searchText.value.trim() } })
  }
}

function handleCommand(command) {
  if (command === 'favorites') {
    router.push('/favorites')
  } else if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.top-nav {
  height: $top-nav-height;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 $spacing-lg;
  background: $bg-white;
}

.nav-left {
  display: flex;
  align-items: center;
  flex: 1;
  overflow: hidden;
}

.logo {
  display: flex;
  align-items: center;
  cursor: pointer;
  margin-right: $spacing-lg;
  flex-shrink: 0;
  color: $primary-color;

  .logo-text {
    font-size: 18px;
    font-weight: 700;
    margin-left: $spacing-sm;
    white-space: nowrap;
  }
}

.nav-menu {
  border-bottom: none;
  height: $top-nav-height;

  :deep(.el-menu-item) {
    height: $top-nav-height;
    line-height: $top-nav-height;
  }
}

.nav-right {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  flex-shrink: 0;
}

.search-input {
  width: 220px;
}

.user-avatar {
  display: flex;
  align-items: center;
  cursor: pointer;
  gap: $spacing-sm;

  .username {
    font-size: 14px;
    color: $text-regular;
  }
}
</style>
