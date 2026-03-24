<template>
  <div class="hot-recommend-page">
    <div class="page-header">
      <h2 class="page-title">热门推荐</h2>
      <p class="page-desc">根据全站用户阅读数据，为你精选最受欢迎的小说</p>
    </div>

    <!-- 排行榜标签页 -->
    <el-tabs v-model="activeTab" class="rank-tabs" type="card">
      <el-tab-pane v-for="cat in categories" :key="cat.key" :label="cat.name" :name="cat.key">
        <div class="rank-list">
          <div v-for="(novel, idx) in cat.novels" :key="novel.id" class="rank-item"
            :class="{ 'rank-gold': idx === 0, 'rank-silver': idx === 1, 'rank-bronze': idx === 2 }">
            <!-- 排名 -->
            <div class="rank-badge" :class="'rank-' + (idx + 1)">
              <span class="rank-num">{{ idx + 1 }}</span>
            </div>

            <!-- 书名首字头像 -->
            <div class="rank-avatar" :style="{ background: avatarColors[idx % avatarColors.length] }">
              {{ novel.title.charAt(0) }}
            </div>

            <!-- 信息区 -->
            <div class="rank-info">
              <div class="rank-title">{{ novel.title }}</div>
              <div class="rank-meta">
                <span class="rank-author">{{ novel.author }}</span>
                <el-tag size="small" effect="plain" round>{{ novel.tag }}</el-tag>
              </div>
            </div>

            <!-- 热度条 -->
            <div class="rank-heat">
              <div class="heat-bar">
                <div class="heat-fill" :style="{ width: novel.heatPercent + '%', background: heatGradients[idx % heatGradients.length] }"></div>
              </div>
              <span class="heat-reads">{{ formatReads(novel.readCount) }} 阅读</span>
            </div>

            <!-- 评分 -->
            <div class="rank-score-area">
              <div class="score-ring" :style="{ '--score-color': getScoreColor(novel.score) }">
                {{ novel.score }}
              </div>
              <span class="score-label">评分</span>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/api/index'

const avatarColors = [
  'linear-gradient(135deg, #ff6b6b, #ee5a24)',
  'linear-gradient(135deg, #ffa502, #ff6348)',
  'linear-gradient(135deg, #3742fa, #1e90ff)',
  'linear-gradient(135deg, #2ed573, #05c46b)',
  'linear-gradient(135deg, #a55eea, #8854d0)',
  'linear-gradient(135deg, #1e90ff, #0652DD)',
  'linear-gradient(135deg, #ff4757, #c44569)',
  'linear-gradient(135deg, #ffa502, #eccc68)'
]

const heatGradients = [
  'linear-gradient(90deg, #ff6b6b, #ee5a24)',
  'linear-gradient(90deg, #ffa502, #ff6348)',
  'linear-gradient(90deg, #3742fa, #70a1ff)',
  'linear-gradient(90deg, #2ed573, #7bed9f)',
  'linear-gradient(90deg, #a55eea, #d2b4fc)',
  'linear-gradient(90deg, #1e90ff, #74b9ff)',
  'linear-gradient(90deg, #ff4757, #ff6b81)',
  'linear-gradient(90deg, #ffa502, #ffeaa7)'
]

const activeTab = ref('hot')
const categories = ref([])

function getScoreColor(score) {
  if (score >= 8) return '#67c23a'
  if (score >= 6) return '#409eff'
  if (score >= 4) return '#e6a23c'
  return '#f56c6c'
}

function formatReads(count) {
  if (!count) return '0'
  if (count >= 10000) return (count / 10000).toFixed(1) + '万'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'k'
  return count.toString()
}

async function loadHotRecommend() {
  try {
    const res = await request.get('/recommend/hot')
    const books = res.data || []

    // 找到最大阅读量用于计算热度百分比
    const maxReads = Math.max(...books.map(b => b.readCount || 0), 1)

    const mapBooks = (list) => list.map((b, i) => ({
      id: b.bookId, title: b.bookName, author: b.author || '未知',
      score: Number(b.score) || 0, tag: b.category || '其他',
      readCount: b.readCount || 0,
      heatPercent: Math.round(((b.readCount || 0) / maxReads) * 100)
    }))

    // 按阅读量排序
    const byReads = [...books].sort((a, b) => (b.readCount || 0) - (a.readCount || 0))
    // 按评分排序
    const byScore = [...books].sort((a, b) => (b.score || 0) - (a.score || 0))
    // 按评论量排序 (热度飙升)
    const byComments = [...books].sort((a, b) => (b.commentTotal || 0) - (a.commentTotal || 0))

    categories.value = [
      { key: 'hot', name: '本周最热', novels: mapBooks(byReads.slice(0, 10)) },
      { key: 'score', name: '高分推荐', novels: mapBooks(byScore.slice(0, 10)) },
      { key: 'rising', name: '热度飙升', novels: mapBooks(byComments.slice(0, 10)) }
    ]
  } catch (e) { /* keep empty */ }
}

onMounted(() => { loadHotRecommend() })
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.hot-recommend-page { padding: $spacing-lg; background: $bg-page; min-height: calc(100vh - $top-nav-height); }
.page-header {
  margin-bottom: $spacing-xl;
  .page-title { font-size: 24px; font-weight: 700; color: $text-primary; margin-bottom: $spacing-xs; }
  .page-desc { font-size: 14px; color: $text-secondary; }
}

.rank-tabs {
  :deep(.el-tabs__header) {
    background: $bg-white; border-radius: 12px 12px 0 0; padding: 4px;
    .el-tabs__item { font-size: 15px; font-weight: 600; padding: 12px 32px; border-radius: 8px; }
    .el-tabs__item.is-active { background: $primary-color; color: #fff; }
  }
  :deep(.el-tabs__content) {
    background: $bg-white; border-radius: 0 0 12px 12px; padding: 20px;
    box-shadow: $box-shadow-light;
  }
}

.rank-list { display: flex; flex-direction: column; gap: 8px; }

.rank-item {
  display: flex; align-items: center; gap: 16px;
  padding: 16px 20px; border-radius: 12px; background: #fafbfc;
  transition: all 0.3s ease; cursor: pointer;
  &:hover { background: #eef1f6; transform: translateX(6px); }
  &.rank-gold { background: linear-gradient(90deg, #fff9e6 0%, #fafbfc 100%); border-left: 4px solid #ffd700; }
  &.rank-silver { background: linear-gradient(90deg, #f5f5f5 0%, #fafbfc 100%); border-left: 4px solid #c0c0c0; }
  &.rank-bronze { background: linear-gradient(90deg, #fef0e5 0%, #fafbfc 100%); border-left: 4px solid #cd7f32; }
}

.rank-badge {
  width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 800; color: #fff;
  background: #c0c4cc;
  &.rank-1 { background: linear-gradient(135deg, #ffd700, #ffaa00); box-shadow: 0 4px 12px rgba(255, 170, 0, 0.4); }
  &.rank-2 { background: linear-gradient(135deg, #c0c0c0, #a0a0a0); box-shadow: 0 4px 12px rgba(160, 160, 160, 0.4); }
  &.rank-3 { background: linear-gradient(135deg, #cd7f32, #b8690e); box-shadow: 0 4px 12px rgba(184, 105, 14, 0.4); }
}

.rank-avatar {
  width: 48px; height: 48px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 800; color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.rank-info {
  flex: 1; min-width: 0;
  .rank-title {
    font-size: 16px; font-weight: 600; color: $text-primary; margin-bottom: 4px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .rank-meta {
    display: flex; align-items: center; gap: 8px;
    .rank-author { font-size: 13px; color: $text-secondary; }
  }
}

.rank-heat {
  width: 180px; flex-shrink: 0;
  .heat-bar {
    height: 8px; background: #eef0f4; border-radius: 4px; overflow: hidden; margin-bottom: 4px;
    .heat-fill { height: 100%; border-radius: 4px; transition: width 0.8s ease; }
  }
  .heat-reads { font-size: 12px; color: $text-secondary; }
}

.rank-score-area {
  flex-shrink: 0; display: flex; flex-direction: column; align-items: center; gap: 2px;
  .score-ring {
    width: 44px; height: 44px; border-radius: 50%;
    border: 3px solid var(--score-color, #409eff);
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; font-weight: 700; color: var(--score-color, #409eff);
  }
  .score-label { font-size: 11px; color: $text-secondary; }
}

@media (max-width: 768px) {
  .rank-heat { display: none; }
  .rank-item { padding: 12px; gap: 10px; }
}
</style>
