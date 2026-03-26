<template>
  <div class="favorites-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">我的收藏</h2>
        <p class="page-desc">管理你收藏的小说，随时回顾精彩作品</p>
      </div>
      <div class="header-stats" v-if="favoriteList.length > 0">
        <div class="stat-item">
          <span class="stat-value">{{ favoriteList.length }}</span>
          <span class="stat-label">收藏总数</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value">{{ avgScore }}</span>
          <span class="stat-label">平均评分</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value">{{ totalWords }}</span>
          <span class="stat-label">总字数</span>
        </div>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchText"
        placeholder="搜索书名或作者..."
        :prefix-icon="Search"
        clearable
        class="search-input"
      />
      <el-select v-model="sortBy" class="sort-select">
        <el-option label="收藏时间" value="time" />
        <el-option label="评分最高" value="score" />
        <el-option label="字数最多" value="words" />
        <el-option label="书名排序" value="name" />
      </el-select>
      <el-button :icon="isList ? Grid : List" @click="isList = !isList" circle />
    </div>

    <!-- 空状态 -->
    <div v-if="filteredNovels.length === 0 && searchText" class="empty-wrapper">
      <el-empty description="没有找到匹配的小说">
        <el-button type="primary" @click="searchText = ''">清除搜索</el-button>
      </el-empty>
    </div>

    <div v-else-if="favoriteList.length === 0" class="empty-wrapper">
      <div class="empty-content">
        <div class="empty-icon">
          <el-icon :size="64" color="#c0c4cc"><Star /></el-icon>
        </div>
        <p class="empty-title">还没有收藏任何小说</p>
        <p class="empty-desc">去推荐页面发现更多好书吧</p>
        <el-button type="primary" round @click="$router.push('/recommend/hot')">探索推荐</el-button>
      </div>
    </div>

    <!-- 列表视图 -->
    <div v-else-if="isList" class="novel-list">
      <div
        v-for="(novel, index) in filteredNovels"
        :key="novel.id"
        class="list-item"
        @click="openNovel(novel.id)"
      >
        <div class="item-avatar" :style="{ background: avatarColors[index % avatarColors.length] }">
          {{ novel.title.charAt(0) }}
        </div>
        <div class="item-info">
          <div class="item-title">{{ novel.title }}</div>
          <div class="item-meta">
            <span class="meta-author">{{ novel.author }}</span>
            <span class="meta-dot">·</span>
            <span class="meta-category">{{ novel.category || '未知分类' }}</span>
            <span class="meta-dot" v-if="novel.wordNumber">·</span>
            <span class="meta-words" v-if="novel.wordNumber">{{ formatWords(novel.wordNumber) }}</span>
          </div>
          <div class="item-tags" v-if="novel.tags">
            <el-tag v-for="tag in novel.tags.split(',').slice(0, 4)" :key="tag" size="small" effect="plain" round>{{ tag.trim() }}</el-tag>
          </div>
        </div>
        <div class="item-score" :style="{ borderColor: scoreColor(novel.score) }">
          <span class="score-num" :style="{ color: scoreColor(novel.score) }">{{ novel.score }}</span>
          <span class="score-text">评分</span>
        </div>
        <div class="item-status">
          <el-tag :type="novel.creationStatus === 1 ? 'success' : 'warning'" size="small" effect="light" round>
            {{ novel.creationStatus === 1 ? '已完结' : '连载中' }}
          </el-tag>
        </div>
        <el-button
          type="danger"
          text
          size="small"
          class="remove-btn"
          @click.stop="handleRemove(novel)"
        >
          <el-icon><Delete /></el-icon>
          取消收藏
        </el-button>
      </div>
    </div>

    <!-- 网格视图 -->
    <el-row v-else :gutter="20" class="novel-grid">
      <el-col :xs="12" :sm="8" :md="6" v-for="(novel, index) in filteredNovels" :key="novel.id">
        <div class="grid-card" @click="openNovel(novel.id)">
          <div class="grid-top" :style="{ background: avatarColors[index % avatarColors.length] }">
            <span class="grid-initial">{{ novel.title.charAt(0) }}</span>
            <div class="grid-score-badge" :style="{ background: scoreColor(novel.score) }">
              {{ novel.score }}
            </div>
            <el-button
              type="danger"
              :icon="Delete"
              circle
              size="small"
              class="grid-remove-btn"
              @click.stop="handleRemove(novel)"
            />
          </div>
          <div class="grid-body">
            <div class="grid-title" :title="novel.title">{{ novel.title }}</div>
            <div class="grid-author">{{ novel.author }}</div>
            <div class="grid-meta">
              <el-tag size="small" effect="plain" round>{{ novel.category || '未知' }}</el-tag>
              <span class="grid-words" v-if="novel.wordNumber">{{ formatWords(novel.wordNumber) }}</span>
            </div>
            <div class="grid-tags" v-if="novel.tags">
              <el-tag v-for="tag in novel.tags.split(',').slice(0, 3)" :key="tag" size="small" type="info" effect="plain" round>{{ tag.trim() }}</el-tag>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 小说详情弹窗 -->
    <NovelDialog v-model:visible="novelDialogVisible" :novel-id="selectedNovelId" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Search, Delete, Star, Grid, List } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/index'
import NovelDialog from '@/components/NovelDialog.vue'

const searchText = ref('')
const sortBy = ref('time')
const isList = ref(true)
const favoriteList = ref([])

const novelDialogVisible = ref(false)
const selectedNovelId = ref(null)

const avatarColors = [
  'linear-gradient(135deg, #667eea, #764ba2)',
  'linear-gradient(135deg, #f093fb, #f5576c)',
  'linear-gradient(135deg, #4facfe, #00f2fe)',
  'linear-gradient(135deg, #43e97b, #38f9d7)',
  'linear-gradient(135deg, #fa709a, #fee140)',
  'linear-gradient(135deg, #a18cd1, #fbc2eb)',
  'linear-gradient(135deg, #fccb90, #d57eeb)',
  'linear-gradient(135deg, #e0c3fc, #8ec5fc)'
]

function openNovel(bookId) {
  selectedNovelId.value = bookId
  novelDialogVisible.value = true
}

function scoreColor(score) {
  if (score >= 8) return '#67c23a'
  if (score >= 6) return '#409eff'
  if (score >= 4) return '#e6a23c'
  return '#f56c6c'
}

function formatWords(num) {
  if (!num) return ''
  if (num >= 10000) return (num / 10000).toFixed(1) + '万字'
  return num + '字'
}

const avgScore = computed(() => {
  if (favoriteList.value.length === 0) return '0'
  const total = favoriteList.value.reduce((sum, n) => sum + (n.score || 0), 0)
  return (total / favoriteList.value.length).toFixed(1)
})

const totalWords = computed(() => {
  const total = favoriteList.value.reduce((sum, n) => sum + (n.wordNumber || 0), 0)
  if (total >= 100000000) return (total / 100000000).toFixed(1) + '亿'
  if (total >= 10000) return (total / 10000).toFixed(0) + '万'
  return total + ''
})

const filteredNovels = computed(() => {
  let novels = [...favoriteList.value]

  if (searchText.value) {
    const kw = searchText.value.toLowerCase()
    novels = novels.filter(n =>
      n.title.toLowerCase().includes(kw) ||
      n.author.toLowerCase().includes(kw) ||
      (n.category || '').toLowerCase().includes(kw)
    )
  }

  switch (sortBy.value) {
    case 'score':
      novels.sort((a, b) => (b.score || 0) - (a.score || 0))
      break
    case 'words':
      novels.sort((a, b) => (b.wordNumber || 0) - (a.wordNumber || 0))
      break
    case 'name':
      novels.sort((a, b) => a.title.localeCompare(b.title, 'zh-CN'))
      break
    default:
      break
  }

  return novels
})

async function loadFavorites() {
  try {
    const res = await request.get('/favorites')
    favoriteList.value = (res.data || []).map(b => ({
      id: b.bookId,
      title: b.bookName || '未知',
      author: b.author || '未知',
      score: Number(b.score) || 0,
      category: b.category || '',
      wordNumber: b.wordNumber || 0,
      tags: b.tags || '',
      creationStatus: b.creationStatus
    }))
  } catch (e) { /* 未登录 */ }
}

async function handleRemove(novel) {
  try {
    await ElMessageBox.confirm(
      `确定要取消收藏《${novel.title}》吗？`,
      '取消收藏',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await request.delete(`/favorites/${novel.id}`)
    favoriteList.value = favoriteList.value.filter(f => f.id !== novel.id)
    ElMessage.success(`已取消收藏《${novel.title}》`)
  } catch { /* cancelled */ }
}

onMounted(() => { loadFavorites() })
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.favorites-page {
  padding: $spacing-lg;
  background: $bg-page;
  min-height: calc(100vh - $top-nav-height);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $spacing-lg;
  background: $bg-white;
  padding: $spacing-lg;
  border-radius: $border-radius-lg;
  box-shadow: $box-shadow-light;

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

.header-stats {
  display: flex;
  align-items: center;
  gap: $spacing-lg;

  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }

  .stat-value {
    font-size: 22px;
    font-weight: 700;
    color: $text-primary;
  }

  .stat-label {
    font-size: 12px;
    color: $text-secondary;
  }

  .stat-divider {
    width: 1px;
    height: 36px;
    background: $border-light;
  }
}

.toolbar {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
  background: $bg-white;
  padding: $spacing-md $spacing-lg;
  border-radius: $border-radius-lg;
  box-shadow: $box-shadow-light;

  .search-input { width: 320px; max-width: 100%; }
  .sort-select { width: 140px; }
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

.empty-content {
  text-align: center;

  .empty-icon { margin-bottom: $spacing-md; }

  .empty-title {
    font-size: 18px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: $spacing-xs;
  }

  .empty-desc {
    font-size: 14px;
    color: $text-secondary;
    margin-bottom: $spacing-lg;
  }
}

/* ========== 列表视图 ========== */
.novel-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.list-item {
  display: flex;
  align-items: center;
  gap: 16px;
  background: $bg-white;
  padding: 18px 24px;
  border-radius: 14px;
  box-shadow: $box-shadow-light;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    transform: translateX(6px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);

    .remove-btn { opacity: 1; }
  }
}

.item-avatar {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 800;
  color: #fff;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
}

.item-info {
  flex: 1;
  min-width: 0;

  .item-title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .item-meta {
    font-size: 13px;
    color: $text-secondary;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 4px;
    flex-wrap: wrap;

    .meta-dot { color: $border-color; }
    .meta-words { color: $primary-color; font-weight: 500; }
  }

  .item-tags {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;

    .el-tag { font-size: 11px; }
  }
}

.item-score {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 3px solid;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .score-num {
    font-size: 16px;
    font-weight: 700;
    line-height: 1;
  }

  .score-text {
    font-size: 9px;
    color: $text-secondary;
    line-height: 1;
    margin-top: 1px;
  }
}

.item-status {
  flex-shrink: 0;
}

.remove-btn {
  opacity: 0;
  transition: opacity 0.3s;
  flex-shrink: 0;
}

/* ========== 网格视图 ========== */
.novel-grid {
  .el-col { margin-bottom: 20px; }
}

.grid-card {
  background: $bg-white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: $box-shadow-light;
  cursor: pointer;
  transition: all 0.3s ease;
  height: 100%;

  &:hover {
    transform: translateY(-6px);
    box-shadow: 0 16px 32px rgba(0, 0, 0, 0.1);

    .grid-remove-btn { opacity: 1; }
  }
}

.grid-top {
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;

  .grid-initial {
    font-size: 42px;
    font-weight: 900;
    color: rgba(255, 255, 255, 0.85);
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }

  .grid-score-badge {
    position: absolute;
    top: 10px;
    left: 10px;
    color: #fff;
    font-size: 13px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 10px;
  }

  .grid-remove-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    opacity: 0;
    transition: opacity 0.3s;
  }
}

.grid-body {
  padding: 14px;

  .grid-title {
    font-size: 15px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .grid-author {
    font-size: 12px;
    color: $text-secondary;
    margin-bottom: 8px;
  }

  .grid-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;

    .grid-words {
      font-size: 12px;
      color: $primary-color;
      font-weight: 500;
    }
  }

  .grid-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;

    .el-tag { font-size: 10px; }
  }
}

@media (max-width: 768px) {
  .page-header { flex-direction: column; gap: $spacing-md; }
  .toolbar { flex-wrap: wrap; .search-input { width: 100%; } }
  .list-item { flex-wrap: wrap; gap: 10px; }
  .item-score { width: 40px; height: 40px; .score-num { font-size: 14px; } }
  .remove-btn { opacity: 1; }
}
</style>
