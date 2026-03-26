<template>
  <div class="search-page">
    <div class="search-header">
      <h2>搜索结果：<span class="keyword">{{ keyword }}</span></h2>
      <p class="result-count">共找到 <strong>{{ totalResults }}</strong> 条相关结果</p>
    </div>

    <div v-if="totalResults === 0 && keyword" class="empty-wrapper">
      <el-empty description="没有找到相关小说" />
    </div>

    <div v-else class="novel-list">
      <div v-for="(item, index) in novelResults" :key="item.id" class="novel-item" @click="openNovel(item.id)">
        <div class="novel-avatar" :style="{ background: avatarColors[index % avatarColors.length] }">
          {{ item.title.charAt(0) }}
        </div>
        <div class="novel-info">
          <div class="novel-title">{{ item.title }}</div>
          <div class="novel-meta">
            <span class="meta-author">{{ item.author }}</span>
            <span class="meta-dot">·</span>
            <span class="meta-category">{{ item.category }}</span>
            <span class="meta-dot" v-if="item.wordNumber">·</span>
            <span class="meta-words" v-if="item.wordNumber">{{ formatWords(item.wordNumber) }}</span>
          </div>
          <div class="novel-tags" v-if="item.tags">
            <el-tag v-for="tag in item.tags.split(',').slice(0, 4)" :key="tag" size="small" effect="plain" round>{{ tag.trim() }}</el-tag>
          </div>
          <p class="novel-desc" v-if="item.desc">{{ item.desc }}</p>
        </div>
        <div class="novel-score" :style="{ borderColor: scoreColor(item.score) }">
          <span class="score-num" :style="{ color: scoreColor(item.score) }">{{ item.score }}</span>
          <span class="score-label">评分</span>
        </div>
        <el-button
          class="fav-btn"
          :type="isFav(item.id) ? 'warning' : 'default'"
          :icon="Star"
          circle
          size="small"
          @click.stop="toggleFav(item.id)"
        />
      </div>
    </div>

    <NovelDialog v-model:visible="novelDialogVisible" :novel-id="selectedNovelId" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/api/index'
import NovelDialog from '@/components/NovelDialog.vue'

const route = useRoute()
const keyword = computed(() => route.query.q || '')
const totalResults = ref(0)
const novelResults = ref([])

const novelDialogVisible = ref(false)
const selectedNovelId = ref(null)
const favSet = ref(new Set())

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

function scoreColor(s) {
  if (s >= 8) return '#67c23a'
  if (s >= 6) return '#409eff'
  if (s >= 4) return '#e6a23c'
  return '#f56c6c'
}

function formatWords(num) {
  if (!num) return ''
  if (num >= 10000) return (num / 10000).toFixed(1) + '万字'
  return num + '字'
}

function isFav(id) { return favSet.value.has(String(id)) }

async function toggleFav(id) {
  const sid = String(id)
  try {
    if (isFav(id)) {
      await request.delete(`/favorites/${sid}`)
      favSet.value.delete(sid)
      favSet.value = new Set(favSet.value)
      ElMessage.success('已取消收藏')
    } else {
      await request.post(`/favorites/${sid}`)
      favSet.value.add(sid)
      favSet.value = new Set(favSet.value)
      ElMessage.success('收藏成功')
    }
  } catch { /* auth error handled by interceptor */ }
}

async function loadFavStatus() {
  try {
    const res = await request.get('/favorites')
    const ids = (res.data || []).map(b => String(b.bookId))
    favSet.value = new Set(ids)
  } catch { /* not logged in */ }
}

async function doSearch() {
  if (!keyword.value) return
  try {
    const res = await request.get('/search', { params: { keyword: keyword.value } })
    const books = res.data || []
    totalResults.value = books.length
    novelResults.value = books.map(b => ({
      id: b.bookId,
      title: b.bookName || '未知',
      author: b.author || '未知',
      category: b.category || '其他',
      score: Number(b.score) || 0,
      wordNumber: b.wordNumber || 0,
      tags: b.tags || '',
      desc: b.bookAbstract || ''
    }))
  } catch (e) { /* interceptor handles */ }
}

watch(keyword, () => { doSearch() }, { immediate: true })
loadFavStatus()
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.search-page { padding: $spacing-lg; min-height: 100%; }

.search-header {
  margin-bottom: $spacing-lg;
  h2 { font-size: 20px; color: $text-primary; margin: 0 0 $spacing-xs 0; .keyword { color: $primary-color; } }
  .result-count { font-size: 13px; color: $text-secondary; margin: 0; }
}

.empty-wrapper {
  display: flex; justify-content: center; align-items: center; min-height: 400px;
  background: $bg-white; border-radius: $border-radius-lg; box-shadow: $box-shadow-light;
}

.novel-list { display: flex; flex-direction: column; gap: 10px; }

.novel-item {
  display: flex; align-items: center; gap: 16px;
  background: $bg-white; padding: 18px 24px; border-radius: 14px;
  box-shadow: $box-shadow-light; cursor: pointer; transition: all 0.3s ease;
  &:hover { transform: translateX(6px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
}

.novel-avatar {
  width: 52px; height: 52px; border-radius: 14px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 800; color: #fff;
  box-shadow: 0 4px 14px rgba(0,0,0,0.1);
}

.novel-info {
  flex: 1; min-width: 0;
  .novel-title { font-size: 16px; font-weight: 600; color: $text-primary; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .novel-meta { font-size: 13px; color: $text-secondary; margin-bottom: 6px; display: flex; align-items: center; gap: 4px; flex-wrap: wrap;
    .meta-dot { color: $border-color; }
    .meta-words { color: $primary-color; font-weight: 500; }
  }
  .novel-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 4px; .el-tag { font-size: 11px; } }
  .novel-desc { font-size: 12px; color: $text-secondary; margin: 0; line-height: 1.5; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}

.novel-score {
  width: 48px; height: 48px; border-radius: 50%; border: 3px solid;
  display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0;
  .score-num { font-size: 16px; font-weight: 700; line-height: 1; }
  .score-label { font-size: 9px; color: $text-secondary; line-height: 1; margin-top: 1px; }
}

.fav-btn { flex-shrink: 0; }
</style>
