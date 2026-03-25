<template>
  <div class="similar-recommend-page">
    <div class="page-header">
      <h2 class="page-title">相似推荐</h2>
      <p class="page-desc">选择一本小说，发现与之相似的作品关系网络</p>
    </div>

    <div class="search-bar">
      <el-select v-model="selectedNovelId" filterable placeholder="搜索或选择一本小说" size="large" class="novel-select" @change="handleNovelChange">
        <el-option v-for="novel in novelOptions" :key="novel.bookId" :label="`${novel.bookName} - ${novel.author}`" :value="novel.bookId" />
      </el-select>
    </div>

    <div class="content-layout">
      <!-- 关系图 -->
      <div class="chart-panel">
        <div class="chart-header">
          <span class="chart-title-text">关系网络图</span>
          <el-tag v-if="centerBook" effect="dark" round>{{ centerBook.bookName }}</el-tag>
        </div>
        <div ref="chartRef" class="relation-chart"></div>
      </div>

      <!-- 侧边栏 -->
      <div class="side-panel">
        <div class="panel-header">
          <h3 class="panel-title"><el-icon><Connection /></el-icon> 相似作品</h3>
          <el-tag size="small" type="info" round>{{ currentSimilarNovels.length }} 部</el-tag>
        </div>
        <el-empty v-if="currentSimilarNovels.length === 0" description="暂无足够相似的作品" :image-size="80" />
        <div class="similar-list" v-else>
          <div class="similar-item" v-for="(novel, index) in currentSimilarNovels" :key="novel.bookId"
            :class="{ 'high-match': novel.similarity >= 70 }">
            <!-- 排名标记 -->
            <div class="rank-indicator" :class="rankClass(index)">{{ index + 1 }}</div>
            <div class="item-avatar" :style="{ background: avatarColors[index % avatarColors.length] }">
              {{ novel.bookName.charAt(0) }}
            </div>
            <div class="item-info">
              <div class="item-title-row">
                <span class="item-title">{{ novel.bookName }}</span>
                <el-button
                  :icon="Star"
                  :type="isFav(novel.bookId) ? 'warning' : ''"
                  size="small"
                  circle
                  class="fav-btn"
                  @click.stop="toggleFav(novel)"
                />
              </div>
              <div class="item-author">{{ novel.author }} · {{ novel.category || '未知分类' }}</div>
              <div class="item-tags" v-if="novel.tags">
                <el-tag v-for="tag in novel.tags.split(',').slice(0, 3)" :key="tag" size="small" effect="plain" round>{{ tag.trim() }}</el-tag>
              </div>
              <div class="item-similarity-bar">
                <div class="sim-bar-bg">
                  <div class="sim-bar-fill" :style="{ width: novel.similarity + '%', background: simGradient(novel.similarity) }"></div>
                </div>
                <span class="sim-label" :style="{ color: simColor(novel.similarity) }">{{ novel.similarity }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Connection, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/api/index'

const chartRef = ref(null)
let chartInstance = null

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

const novelOptions = ref([])
const selectedNovelId = ref(null)
const centerBook = ref(null)
const currentSimilarNovels = ref([])
const favSet = ref(new Set())

function rankClass(index) {
  if (index === 0) return 'gold'
  if (index === 1) return 'silver'
  if (index === 2) return 'bronze'
  return ''
}

function simColor(val) {
  if (val >= 80) return '#67c23a'
  if (val >= 60) return '#409eff'
  if (val >= 40) return '#e6a23c'
  return '#909399'
}

function simGradient(val) {
  if (val >= 80) return 'linear-gradient(90deg, #43e97b, #38f9d7)'
  if (val >= 60) return 'linear-gradient(90deg, #667eea, #764ba2)'
  if (val >= 40) return 'linear-gradient(90deg, #e6a23c, #f7c948)'
  return 'linear-gradient(90deg, #909399, #c0c4cc)'
}

function isFav(bookId) {
  return favSet.value.has(String(bookId))
}

async function toggleFav(novel) {
  const bid = String(novel.bookId)
  try {
    if (isFav(bid)) {
      await request.delete(`/favorites/${bid}`)
      favSet.value.delete(bid)
      ElMessage.success(`已取消收藏《${novel.bookName}》`)
    } else {
      await request.post(`/favorites/${bid}`)
      favSet.value.add(bid)
      ElMessage.success(`已收藏《${novel.bookName}》`)
    }
  } catch (e) {
    ElMessage.warning('请先登录后再收藏')
  }
}

async function loadFavStatus() {
  try {
    const res = await request.get('/favorites')
    const list = res.data || []
    favSet.value = new Set(list.map(b => String(b.bookId)))
  } catch (e) { /* 未登录 */ }
}

const nodeColors = ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#a18cd1', '#fccb90']

async function loadBookOptions() {
  try {
    const res = await request.get('/recommend/book-options')
    novelOptions.value = res.data || []
    if (novelOptions.value.length > 0 && !selectedNovelId.value) {
      selectedNovelId.value = novelOptions.value[0].bookId
      loadSimilar(selectedNovelId.value)
    }
  } catch (e) { /* keep empty */ }
}

async function loadSimilar(bookId) {
  try {
    const res = await request.get(`/recommend/similar/${bookId}`)
    const data = res.data || {}
    centerBook.value = data.center
    currentSimilarNovels.value = data.similar || []
    nextTick(() => initChart())
  } catch (e) { /* keep empty */ }
}

function handleNovelChange(bookId) {
  loadSimilar(bookId)
}

function initChart() {
  if (!chartRef.value || !centerBook.value) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)

  const centerNode = {
    name: centerBook.value.bookName,
    symbolSize: 80,
    itemStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
        { offset: 0, color: '#667eea' }, { offset: 1, color: '#764ba2' }
      ]),
      shadowBlur: 25, shadowColor: 'rgba(102, 126, 234, 0.5)',
      borderColor: '#fff', borderWidth: 3
    },
    label: { fontSize: 14, fontWeight: 'bold', color: '#303133' }
  }

  const similarNodes = currentSimilarNovels.value.map((novel, index) => ({
    name: novel.bookName,
    symbolSize: 30 + (novel.similarity || 0) * 0.4,
    itemStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
        { offset: 0, color: nodeColors[index % nodeColors.length] },
        { offset: 1, color: nodeColors[(index + 1) % nodeColors.length] }
      ]),
      shadowBlur: 12, shadowColor: 'rgba(0, 0, 0, 0.15)',
      borderColor: '#fff', borderWidth: 2
    },
    label: { fontSize: 11, color: '#606266' }
  }))

  const links = currentSimilarNovels.value.map(novel => ({
    source: centerBook.value.bookName,
    target: novel.bookName,
    value: novel.similarity,
    lineStyle: {
      width: 1 + (novel.similarity || 0) / 25,
      color: novel.similarity >= 60 ? 'rgba(102, 126, 234, 0.6)' : 'rgba(192, 196, 204, 0.5)',
      curveness: 0.15,
      type: novel.similarity >= 50 ? 'solid' : 'dashed'
    },
    label: { show: true, formatter: `${novel.similarity}%`, fontSize: 11, color: '#909399', backgroundColor: 'rgba(255,255,255,0.8)', padding: [2, 4], borderRadius: 3 }
  }))

  chartInstance.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(50, 50, 50, 0.9)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#fff', fontSize: 13 },
      formatter: params => {
        if (params.dataType === 'node') return `<strong>${params.name}</strong>`
        if (params.dataType === 'edge') return `${params.data.source} → ${params.data.target}<br/>相似度: ${params.data.value}%`
        return ''
      }
    },
    animationDurationUpdate: 800,
    animationEasingUpdate: 'quinticInOut',
    series: [{
      type: 'graph', layout: 'force',
      force: { repulsion: 700, gravity: 0.08, edgeLength: [100, 280], layoutAnimation: true, friction: 0.6 },
      roam: true, draggable: true, symbol: 'circle',
      data: [centerNode, ...similarNodes], links,
      label: { show: true, position: 'bottom', distance: 10 },
      edgeLabel: { show: true, fontSize: 11 },
      emphasis: { focus: 'adjacency', lineStyle: { width: 5 }, itemStyle: { shadowBlur: 25 } },
      lineStyle: { opacity: 0.8 }
    }]
  })
}

const handleResize = () => { chartInstance?.resize() }

onMounted(() => {
  loadBookOptions()
  loadFavStatus()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.similar-recommend-page { padding: $spacing-lg; background: $bg-page; min-height: calc(100vh - $top-nav-height); }
.page-header { margin-bottom: $spacing-lg; .page-title { font-size: 24px; font-weight: 700; color: $text-primary; margin-bottom: $spacing-xs; } .page-desc { font-size: 14px; color: $text-secondary; } }
.search-bar { margin-bottom: $spacing-lg; background: $bg-white; padding: $spacing-md $spacing-lg; border-radius: $border-radius-lg; box-shadow: $box-shadow-light; .novel-select { width: 400px; max-width: 100%; } }

.content-layout { display: flex; gap: $spacing-lg; align-items: flex-start; }

.chart-panel {
  flex: 1; background: $bg-white; border-radius: $border-radius-lg; box-shadow: $box-shadow-light;
  overflow: hidden; min-height: 560px;
  .chart-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: $spacing-md $spacing-lg; border-bottom: 1px solid #f0f2f5;
    .chart-title-text { font-size: 15px; font-weight: 600; color: $text-primary; }
  }
  .relation-chart { width: 100%; height: 520px; }
}

.side-panel {
  width: 400px; flex-shrink: 0; background: $bg-white; border-radius: $border-radius-lg;
  box-shadow: $box-shadow-light; max-height: 600px; overflow-y: auto;
  &::-webkit-scrollbar { width: 4px; } &::-webkit-scrollbar-thumb { background: $border-color; border-radius: 2px; }
}

.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: $spacing-lg $spacing-lg $spacing-md;
  border-bottom: 1px solid #f0f2f5; position: sticky; top: 0; background: $bg-white; z-index: 2;
}

.panel-title {
  font-size: 16px; font-weight: 600; color: $text-primary; margin: 0;
  display: flex; align-items: center; gap: $spacing-sm; .el-icon { color: $primary-color; }
}

.similar-list { padding: $spacing-md; display: flex; flex-direction: column; gap: $spacing-sm; }

.similar-item {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 14px; border-radius: 14px; background: #f9fafb;
  border: 1px solid transparent;
  transition: all 0.3s ease; position: relative;

  &:hover { background: #f0f4ff; border-color: rgba(102, 126, 234, 0.2); transform: translateX(3px); }
  &.high-match { background: linear-gradient(135deg, #f0fdf4 0%, #f0f7ff 100%); border-color: rgba(67, 233, 123, 0.2); }
}

.rank-indicator {
  position: absolute; top: 8px; right: 10px;
  width: 22px; height: 22px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 800; color: #909399; background: #f0f2f5;

  &.gold { background: linear-gradient(135deg, #ffd700, #ffb800); color: #fff; box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3); }
  &.silver { background: linear-gradient(135deg, #c0c0c0, #a8a8a8); color: #fff; }
  &.bronze { background: linear-gradient(135deg, #cd7f32, #b8742e); color: #fff; }
}

.item-avatar {
  width: 48px; height: 48px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 800; color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.item-info {
  flex: 1; min-width: 0;

  .item-title-row {
    display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 4px;
    .fav-btn { flex-shrink: 0; }
  }
  .item-title { font-size: 14px; font-weight: 600; color: $text-primary; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; min-width: 0; }
  .item-author { font-size: 12px; color: $text-secondary; margin-bottom: 6px; }
  .item-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 8px; .el-tag { font-size: 10px; } }
}

.item-similarity-bar {
  display: flex; align-items: center; gap: 10px;

  .sim-bar-bg {
    flex: 1; height: 6px; background: #f0f2f5; border-radius: 3px; overflow: hidden;
    .sim-bar-fill { height: 100%; border-radius: 3px; transition: width 0.8s ease; }
  }
  .sim-label { font-size: 13px; font-weight: 700; min-width: 40px; text-align: right; }
}

@media (max-width: 1024px) { .content-layout { flex-direction: column; } .side-panel { width: 100%; max-height: none; } }
</style>
