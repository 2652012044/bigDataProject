<template>
  <div class="favorites-page">
    <div class="page-header">
      <h2 class="page-title">我的收藏</h2>
      <p class="page-desc">管理你收藏的小说，随时回顾精彩作品</p>
    </div>

    <div class="toolbar">
      <el-input
        v-model="searchText"
        placeholder="搜索收藏的小说..."
        :prefix-icon="Search"
        clearable
        class="search-input"
      />
      <el-select v-model="sortBy" placeholder="排序方式" class="sort-select">
        <el-option label="收藏时间" value="collectDate" />
        <el-option label="评分" value="score" />
        <el-option label="书名" value="title" />
      </el-select>
    </div>

    <!-- Empty state -->
    <div v-if="filteredNovels.length === 0 && searchText" class="empty-wrapper">
      <el-empty description="没有找到匹配的小说">
        <el-button type="primary" @click="searchText = ''">清除搜索</el-button>
      </el-empty>
    </div>

    <div v-else-if="displayNovels.length === 0" class="empty-wrapper">
      <el-empty description="还没有收藏任何小说">
        <el-button type="primary" @click="goToRecommend">去看看推荐</el-button>
      </el-empty>
    </div>

    <!-- Novel grid -->
    <el-row v-else :gutter="20" class="novel-grid">
      <el-col
        :xs="12" :sm="8" :md="6"
        v-for="novel in filteredNovels"
        :key="novel.id"
      >
        <div class="novel-card">
          <div class="card-cover" :style="{ background: novel.coverColor }">
            <div class="cover-overlay">
              <el-button
                type="danger"
                :icon="Delete"
                circle
                size="small"
                class="remove-btn"
                @click.stop="handleRemove(novel)"
              />
            </div>
            <div class="score-badge">{{ novel.score }}</div>
          </div>
          <div class="card-body">
            <div class="card-title" :title="novel.title">{{ novel.title }}</div>
            <div class="card-author">{{ novel.author }}</div>
            <div class="card-date">
              <el-icon><Clock /></el-icon>
              {{ novel.collectDate }}
            </div>
            <div class="card-actions">
              <el-button size="small" type="primary" text>
                <el-icon><Reading /></el-icon>
                阅读
              </el-button>
              <el-button size="small" type="danger" text @click="handleRemove(novel)">
                <el-icon><Delete /></el-icon>
                取消收藏
              </el-button>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Search, Delete, Clock, Reading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/index'

const router = useRouter()
const userStore = useUserStore()

const searchText = ref('')
const sortBy = ref('collectDate')
const favoriteList = ref([])

const coverColors = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  'linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)',
  'linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)'
]

async function loadFavorites() {
  try {
    const res = await request.get('/favorites')
    favoriteList.value = (res.data || []).map((b, i) => ({
      id: b.bookId,
      title: b.bookName || '未知',
      author: b.author || '未知',
      score: Number(b.score) || 0,
      collectDate: new Date().toISOString().slice(0, 10),
      coverColor: coverColors[i % coverColors.length]
    }))
  } catch (e) { /* 未登录或其他错误 */ }
}

const displayNovels = computed(() => {
  return favoriteList.value.length > 0 ? favoriteList.value : []
})

const filteredNovels = computed(() => {
  let novels = [...displayNovels.value]

  // Filter by search text
  if (searchText.value) {
    const keyword = searchText.value.toLowerCase()
    novels = novels.filter(
      (n) =>
        n.title.toLowerCase().includes(keyword) ||
        n.author.toLowerCase().includes(keyword)
    )
  }

  // Sort
  if (sortBy.value === 'collectDate') {
    novels.sort((a, b) => new Date(b.collectDate) - new Date(a.collectDate))
  } else if (sortBy.value === 'score') {
    novels.sort((a, b) => b.score - a.score)
  } else if (sortBy.value === 'title') {
    novels.sort((a, b) => a.title.localeCompare(b.title, 'zh-CN'))
  }

  return novels
})

const handleRemove = async (novel) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消收藏《${novel.title}》吗？`,
      '取消收藏',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await request.delete(`/favorites/${novel.id}`)
    favoriteList.value = favoriteList.value.filter(f => f.id !== novel.id)
    ElMessage.success(`已取消收藏《${novel.title}》`)
  } catch {
    // User cancelled
  }
}

const goToRecommend = () => {
  router.push('/recommend/hot')
}

onMounted(() => {
  loadFavorites()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.favorites-page {
  padding: $spacing-lg;
  background: $bg-page;
  min-height: calc(100vh - $top-nav-height);
}

.page-header {
  margin-bottom: $spacing-lg;

  .page-title {
    font-size: 24px;
    font-weight: 700;
    color: $text-primary;
    margin-bottom: $spacing-xs;
  }

  .page-desc {
    font-size: 14px;
    color: $text-secondary;
  }
}

.toolbar {
  display: flex;
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
  background: $bg-white;
  padding: $spacing-md $spacing-lg;
  border-radius: $border-radius-lg;
  box-shadow: $box-shadow-light;

  .search-input {
    width: 320px;
    max-width: 100%;
  }

  .sort-select {
    width: 160px;
  }
}

.empty-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: $bg-white;
  border-radius: $border-radius-lg;
  box-shadow: $box-shadow-light;
}

.novel-grid {
  .el-col {
    margin-bottom: 20px;
  }
}

.novel-card {
  background: $bg-white;
  border-radius: $border-radius-lg;
  overflow: hidden;
  box-shadow: $box-shadow-light;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
  height: 100%;

  &:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);

    .cover-overlay {
      opacity: 1;
    }
  }
}

.card-cover {
  height: 180px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;

  .cover-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: flex-start;
    justify-content: flex-end;
    padding: $spacing-sm;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .score-badge {
    position: absolute;
    bottom: $spacing-sm;
    left: $spacing-sm;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(8px);
    color: #fff;
    font-size: 14px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 16px;
    z-index: 1;
  }

  .remove-btn {
    z-index: 2;
  }
}

.card-body {
  padding: $spacing-md;

  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-bottom: $spacing-xs;
  }

  .card-author {
    font-size: 13px;
    color: $text-secondary;
    margin-bottom: $spacing-sm;
  }

  .card-date {
    font-size: 12px;
    color: $text-placeholder;
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: $spacing-sm;
  }

  .card-actions {
    display: flex;
    justify-content: space-between;
    border-top: 1px solid $border-light;
    padding-top: $spacing-sm;
    margin-top: $spacing-xs;

    .el-button {
      font-size: 12px;
    }
  }
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;

    .search-input,
    .sort-select {
      width: 100%;
    }
  }
}
</style>
